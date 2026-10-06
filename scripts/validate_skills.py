#!/usr/bin/env python3
"""Validate local or public Claude skill packages without dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import unquote, urlsplit


TEXT_SUFFIXES = {".json", ".md", ".sh", ".txt", ".yaml", ".yml"}
MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]]*]\(\s*(<[^>\n]+>|[^)\s]+)(?:\s+[\"'][^)]*)?\)"
)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
PLACEHOLDER_RE = re.compile(
    r"\{\{\s*[A-Za-z][A-Za-z0-9_.-]*\s*}}"
    r"|__[A-Z][A-Z0-9_-]*__"
)
MUTATION_RE = re.compile(
    r"\b(?:append(?:s|ed|ing)?|commit(?:s|ted|ting)?|creat(?:e|es|ed|ing)|"
    r"delet(?:e|es|ed|ing)|deploy(?:s|ed|ing)?|edit(?:s|ed|ing)?|"
    r"modif(?:y|ies|ied|ying)|push(?:es|ed|ing)?|releas(?:e|es|ed|ing)|"
    r"remov(?:e|es|ed|ing)|renam(?:e|es|ed|ing)|restart(?:s|ed|ing)?|"
    r"rewrit(?:e|es|ten|ing)|ship(?:s|ped|ping)?|updat(?:e|es|ed|ing)|"
    r"writ(?:e|es|ten|ing))\b",
    re.IGNORECASE,
)
EXPLICIT_PROHIBITION_RE = re.compile(r"\b(?:do not|don't|must not|never)\b", re.IGNORECASE)
MANIFEST_MODES = {"adapter", "symlink", "overlay", "dynamic"}
MAX_TEXT_BYTES = 2_000_000
RISK_PATTERNS = (
    ("origin-main", re.compile(r"\borigin/main\b"), "hard-coded origin/main workflow reference"),
    ("branches-main", re.compile(r"\bbranches/main\b"), "hard-coded branches/main workflow reference"),
    (
        "nondeterministic-k",
        re.compile(r"\bK\s*=\s*2\s*[-–—]\s*3\b", re.IGNORECASE),
        "nondeterministic K=2-3 reviewer count",
    ),
    (
        "unsupported-policy",
        re.compile(r"\bpolicy\.allow_implicit_invocation\b"),
        "unsupported policy.allow_implicit_invocation setting",
    ),
)


@dataclass(frozen=True, order=True)
class Finding:
    severity: str
    path: str
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class BashFence:
    path: Path
    line: int
    code: str


@dataclass
class Skill:
    directory: Path
    markdown_files: list[Path]
    text_files: list[Path]

    @property
    def skill_file(self) -> Path:
        return self.directory / "SKILL.md"


class Validator:
    def __init__(
        self,
        roots: Sequence[Path],
        manifest: Path | None = None,
        contract: Path | None = None,
    ) -> None:
        self.roots = tuple(sorted({Path(root).absolute() for root in roots}, key=str))
        self.manifest = manifest.absolute() if manifest else None
        self.contract = contract.absolute() if contract else None
        self.findings: list[Finding] = []
        self.skills: list[Skill] = []
        self.bash_fences: list[BashFence] = []
        self.checked_markdown: set[Path] = set()
        self.shellcheck = shutil.which("shellcheck")

    def add(
        self,
        severity: str,
        path: Path | str,
        line: int,
        code: str,
        message: str,
    ) -> None:
        self.findings.append(Finding(severity, str(path), line, code, message))

    def validate(self) -> list[Finding]:
        for root in self.roots:
            self._scan_root(root)
        self.skills.sort(key=lambda skill: str(skill.directory))
        for skill in self.skills:
            self._validate_skill(skill)
        if self.manifest:
            self._validate_manifest(self.manifest)
        if self.contract:
            self._validate_shared_contract(self.contract)
        self._validate_bash_fences()
        if not self.shellcheck:
            self.add(
                "INFO",
                "-",
                0,
                "shellcheck-unavailable",
                "shellcheck not found; bash fences were not linted with shellcheck",
            )
        self.findings.sort()
        return self.findings

    def _validate_shared_contract(self, path: Path) -> None:
        expected = self._read_text(path)
        if expected is None:
            return
        for skill in self.skills:
            local = skill.directory / "references" / "loop-contract.md"
            actual = self._read_text(local)
            if actual is None:
                self.add(
                    "ERROR",
                    local,
                    0,
                    "missing-loop-contract",
                    "skill must include the shared loop contract",
                )
            elif actual != expected:
                self.add(
                    "ERROR",
                    local,
                    0,
                    "loop-contract-drift",
                    "package-local loop contract differs from the canonical contract",
                )

    def _scan_root(self, root: Path) -> None:
        # SECURITY-REVIEW: Roots are untrusted CLI paths; lstat and scandir are used
        # without following symlinks, and failures are reported without file contents.
        try:
            root.lstat()
        except OSError:
            self.add("ERROR", root, 0, "missing-root", "root cannot be accessed")
            return
        if root.is_symlink():
            self._check_symlink(root)
            self.add("ERROR", root, 0, "symlink-root", "root must not be a symlink")
            return
        if not root.is_dir():
            self.add("ERROR", root, 0, "invalid-root", "root is not a directory")
            return

        directories: dict[Path, list[Path]] = {}
        stack = [root]
        while stack:
            directory = stack.pop()
            files: list[Path] = []
            try:
                entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
            except OSError:
                self.add("ERROR", directory, 0, "unreadable-directory", "directory cannot be scanned")
                continue
            for entry in entries:
                path = Path(entry.path)
                try:
                    if entry.is_symlink():
                        self._check_symlink(path)
                    elif entry.is_dir(follow_symlinks=False):
                        stack.append(path)
                    elif entry.is_file(follow_symlinks=False):
                        files.append(path)
                except OSError:
                    self.add("ERROR", path, 0, "unreadable-entry", "filesystem entry cannot be inspected")
            directories[directory] = files

        skill_directories = sorted(
            (
                directory
                for directory, files in directories.items()
                if any(path.name == "SKILL.md" for path in files)
            ),
            key=str,
        )
        for directory in skill_directories:
            owned_files = [
                path
                for candidate, paths in directories.items()
                if candidate == directory
                or (
                    candidate.is_relative_to(directory)
                    and not any(
                        other != directory
                        and candidate.is_relative_to(other)
                        for other in skill_directories
                    )
                )
                for path in paths
            ]
            markdown = sorted((path for path in owned_files if path.suffix.lower() == ".md"), key=str)
            text = sorted(
                (
                    path
                    for path in owned_files
                    if path.suffix.lower() in TEXT_SUFFIXES or path.name == "SKILL.md"
                ),
                key=str,
            )
            self.skills.append(Skill(directory, markdown, text))

    def _check_symlink(self, path: Path) -> None:
        # SECURITY-REVIEW: Symlink targets are untrusted filesystem data. Resolution
        # is inspection-only and recursive links are never traversed.
        try:
            target = path.resolve(strict=True)
        except FileNotFoundError:
            self.add("ERROR", path, 0, "broken-symlink", "symlink target is missing")
            return
        except (OSError, RuntimeError):
            self.add("ERROR", path, 0, "recursive-symlink", "symlink resolves recursively")
            return
        parent = path.parent.resolve(strict=True)
        target_is_ancestor = parent == target or parent.is_relative_to(target)
        if target_is_ancestor:
            self.add(
                "ERROR",
                path,
                0,
                "nested-self-symlink",
                "symlink targets its own directory or an ancestor",
            )

    def _validate_skill(self, skill: Skill) -> None:
        text = self._read_text(skill.skill_file)
        if text is None:
            return
        lines = text.splitlines()
        if len(lines) >= 500:
            self.add(
                "ERROR",
                skill.skill_file,
                500,
                "skill-too-long",
                "SKILL.md must contain fewer than 500 lines",
            )
        frontmatter, _ = self._parse_frontmatter(skill.skill_file, lines)
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not name:
            self.add("ERROR", skill.skill_file, 1, "missing-name", "frontmatter name is required")
        elif name != skill.directory.name:
            self.add(
                "ERROR",
                skill.skill_file,
                1,
                "name-directory-mismatch",
                "frontmatter name must match the skill directory name",
            )
        if not description:
            self.add(
                "ERROR",
                skill.skill_file,
                1,
                "missing-description",
                "frontmatter description is required",
            )
        disable = frontmatter.get("disable-model-invocation")
        if disable is not None and disable not in {"true", "false"}:
            self.add(
                "ERROR",
                skill.skill_file,
                1,
                "invalid-disable-model-invocation",
                "disable-model-invocation must be true or false",
            )

        for path in skill.markdown_files:
            markdown = self._read_text(path)
            if markdown is not None:
                self.checked_markdown.add(path.absolute())
                self._validate_markdown(skill, path, markdown, text)
        for path in skill.text_files:
            if path in skill.markdown_files:
                continue
            content = self._read_text(path)
            if content is not None:
                self._validate_placeholders(skill, path, content, text)
                self._validate_risky_patterns(path, content)

    def _parse_frontmatter(self, path: Path, lines: list[str]) -> tuple[dict[str, str], int]:
        if not lines or lines[0].strip() != "---":
            self.add("ERROR", path, 1, "missing-frontmatter", "SKILL.md must start with frontmatter")
            return {}, 0
        values: dict[str, str] = {}
        for index in range(1, len(lines)):
            line = lines[index]
            if line.strip() == "---":
                return values, index + 1
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
            if not match:
                self.add(
                    "ERROR",
                    path,
                    index + 1,
                    "invalid-frontmatter",
                    "frontmatter must use simple key: value entries",
                )
                continue
            key, value = match.groups()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[key] = value
        self.add("ERROR", path, 1, "unclosed-frontmatter", "frontmatter closing delimiter is missing")
        return values, len(lines)

    def _validate_markdown(self, skill: Skill, path: Path, text: str, owner_text: str) -> None:
        self._validate_links(path, text, skill.directory)
        self._validate_fences(path, text)
        self._validate_placeholders(skill, path, text, owner_text)
        self._validate_risky_patterns(path, text)
        self._validate_reviewer_counts(path, text)

    def _validate_links(self, path: Path, text: str, owner: Path | None = None) -> None:
        owner_root = owner.resolve(strict=True) if owner else None
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in MARKDOWN_LINK_RE.finditer(line):
                destination = match.group(1).strip("<>")
                if PLACEHOLDER_RE.search(destination):
                    continue
                split = urlsplit(destination)
                if split.scheme or split.netloc or destination.startswith(("#", "/")):
                    continue
                relative = unquote(split.path)
                if not relative:
                    continue
                # SECURITY-REVIEW: Markdown destinations are untrusted. Existence is
                # checked only; targets are never opened or executed.
                target = path.parent / relative
                try:
                    resolved_target = target.resolve(strict=False)
                except (OSError, RuntimeError):
                    resolved_target = target.absolute()
                if owner_root is not None and not resolved_target.is_relative_to(owner_root):
                    self.add(
                        "ERROR",
                        path,
                        line_number,
                        "package-link-escape",
                        "relative Markdown link escapes the owning skill package",
                    )
                    continue
                if not target.exists():
                    self.add(
                        "ERROR",
                        path,
                        line_number,
                        "broken-relative-link",
                        "relative Markdown link target does not exist",
                    )

    def _validate_fences(self, path: Path, text: str) -> None:
        opening: tuple[str, int, int, str] | None = None
        code_lines: list[str] = []
        for line_number, line in enumerate(text.splitlines(), 1):
            match = FENCE_RE.match(line)
            if opening is None:
                if not match:
                    continue
                marker, info = match.groups()
                language = info.strip().split(maxsplit=1)[0] if info.strip() else ""
                if not language:
                    self.add(
                        "ERROR",
                        path,
                        line_number,
                        "untagged-fence",
                        "code fence must include a language tag",
                    )
                opening = (marker[0], len(marker), line_number, language.lower())
                code_lines = []
                continue
            marker_character, marker_length, opening_line, language = opening
            close_re = rf"^\s*{re.escape(marker_character)}{{{marker_length},}}\s*$"
            if re.match(close_re, line):
                if language in {"bash", "sh", "shell"}:
                    self.bash_fences.append(BashFence(path, opening_line, "\n".join(code_lines) + "\n"))
                opening = None
                code_lines = []
            else:
                code_lines.append(line)
        if opening is not None:
            self.add(
                "ERROR",
                path,
                opening[2],
                "unclosed-fence",
                "code fence closing delimiter is missing",
            )

    def _validate_placeholders(self, skill: Skill, path: Path, text: str, owner_text: str) -> None:
        is_template = "templates" in path.relative_to(skill.directory).parts
        documented, documentation_lines = self._template_documentation(owner_text)
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in PLACEHOLDER_RE.finditer(line):
                placeholder = match.group(0)
                if not is_template:
                    if (
                        path == skill.skill_file
                        and line_number in documentation_lines
                        and placeholder in documented
                    ):
                        continue
                    self.add(
                        "ERROR",
                        path,
                        line_number,
                        "placeholder-outside-template",
                        "unresolved placeholder is only allowed inside templates",
                    )
                else:
                    if placeholder in documented:
                        continue
                    self.add(
                        "ERROR",
                        path,
                        line_number,
                        "undocumented-placeholder",
                        "template placeholder is not documented by the owning SKILL.md",
                    )

    def _template_documentation(self, owner_text: str) -> tuple[set[str], set[int]]:
        documented: set[str] = set()
        documentation_lines: set[int] = set()
        in_templates = False
        for line_number, line in enumerate(owner_text.splitlines(), 1):
            heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
            if heading:
                in_templates = bool(re.fullmatch(r"templates?", heading.group(1), re.IGNORECASE))
                continue
            if not in_templates or not re.match(r"^\s*[-*+]\s+\S", line):
                continue
            placeholders = {match.group(0) for match in PLACEHOLDER_RE.finditer(line)}
            if placeholders:
                documented.update(placeholders)
                documentation_lines.add(line_number)
        return documented, documentation_lines

    def _validate_risky_patterns(self, path: Path, text: str) -> None:
        lines = text.splitlines()
        for line_number, line in enumerate(lines, 1):
            for code, pattern, message in RISK_PATTERNS:
                if pattern.search(line):
                    self.add("ERROR", path, line_number, code, message)
            if re.fullmatch(r"\s*(?:[$>]\s*)?git\s+remote\s+-v\s*", line):
                self.add(
                    "ERROR",
                    path,
                    line_number,
                    "bare-git-remote",
                    "bare git remote -v may disclose remote credentials",
                )
            force_instruction = re.search(
                r"(?:--force(?:-with-lease)?|--no-verify|\bforce[- ]push\b)",
                line,
                re.IGNORECASE,
            )
            previous = lines[line_number - 2] if line_number > 1 else ""
            current_clause = ""
            if force_instruction:
                current_clause = re.split(r"[.;!?]", line[: force_instruction.start()])[-1]
            same_line_prohibition = bool(EXPLICIT_PROHIBITION_RE.search(current_clause))
            continued_prohibition = bool(
                EXPLICIT_PROHIBITION_RE.search(previous)
                and not re.search(r"[.!?;:]\s*$", previous)
            )
            if force_instruction and not (same_line_prohibition or continued_prohibition):
                self.add(
                    "ERROR",
                    path,
                    line_number,
                    "unsafe-git-instruction",
                    "force or no-verify instruction must be an explicit prohibition",
                )

    def _validate_reviewer_counts(self, path: Path, text: str) -> None:
        lines = text.splitlines()
        stated_counts: set[int] = set()
        for index, line in enumerate(lines):
            match = re.search(
                r"(?<![-–—])\b(\d+)\s+(?:independent\s+)?reviewers?\b",
                line,
                re.IGNORECASE,
            )
            if not match:
                continue
            expected = int(match.group(1))
            stated_counts.add(expected)
            following = lines[index + 1 : index + 16]
            while following and not following[0].strip():
                following.pop(0)
            bullets = 0
            for candidate in following:
                if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\S", candidate):
                    bullets += 1
                elif candidate.strip():
                    break
            if bullets and bullets != expected:
                self.add(
                    "ERROR",
                    path,
                    index + 1,
                    "reviewer-count-mismatch",
                    "stated reviewer count does not match the following reviewer list",
                )
        if len(stated_counts) > 1:
            self.add(
                "ERROR",
                path,
                1,
                "reviewer-count-conflict",
                "file contains conflicting explicit reviewer counts",
            )

    def _validate_bash_fences(self) -> None:
        bash = shutil.which("bash")
        for fence in sorted(self.bash_fences, key=lambda item: (str(item.path), item.line)):
            if not bash:
                self.add("ERROR", fence.path, fence.line, "bash-unavailable", "bash is unavailable")
                continue
            # SECURITY-REVIEW: Fence text is untrusted. It is passed on stdin to
            # syntax/lint tools without shell=True and is never executed or printed.
            syntax = subprocess.run(
                [bash, "-n"],
                input=fence.code,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if syntax.returncode:
                self.add(
                    "ERROR",
                    fence.path,
                    fence.line,
                    "bash-syntax",
                    "bash fence failed bash -n syntax validation",
                )
            if self.shellcheck:
                lint = subprocess.run(
                    [self.shellcheck, "-s", "bash", "-"],
                    input=fence.code,
                    text=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                if lint.returncode:
                    self.add(
                        "ERROR",
                        fence.path,
                        fence.line,
                        "shellcheck",
                        "bash fence failed shellcheck",
                    )

    def _validate_manifest(self, path: Path) -> None:
        text = self._read_text(path)
        if text is None:
            return
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            self.add("ERROR", path, 0, "invalid-manifest", "manifest is not valid JSON")
            return
        if not isinstance(data, dict):
            self.add("ERROR", path, 0, "invalid-manifest", "manifest must be a JSON object")
            return
        allowed_roots = self._manifest_allowed_roots(path, data)
        mappings = self._manifest_mappings(path, data)
        edges: dict[Path, Path] = {}
        commands: set[str] = set()
        wrappers: set[Path] = set()
        signatures: set[str] = set()
        for mapping in mappings:
            if not isinstance(mapping, dict):
                self.add("ERROR", path, 0, "invalid-mapping", "manifest mappings must be objects")
                continue
            command = mapping.get("command")
            wrapper = mapping.get("wrapper")
            source = mapping.get("source")
            mode = mapping.get("mode")
            signature = json.dumps(mapping, sort_keys=True, separators=(",", ":"))
            if signature in signatures:
                self.add("ERROR", path, 0, "duplicate-mapping", "manifest contains a duplicate mapping")
            signatures.add(signature)
            if not isinstance(command, str) or not command.strip():
                self.add("ERROR", path, 0, "missing-command", "manifest mapping is missing command")
            elif command.strip() in commands:
                self.add("ERROR", path, 0, "duplicate-command", "manifest commands must be unique")
            else:
                commands.add(command.strip())
            if not isinstance(wrapper, str) or not wrapper.strip():
                self.add("ERROR", path, 0, "missing-wrapper", "manifest mapping is missing wrapper")
            if not isinstance(source, str) or not source.strip():
                self.add("ERROR", path, 0, "missing-source", "manifest mapping is missing source")
            valid_mode = isinstance(mode, str) and mode in MANIFEST_MODES
            if not valid_mode:
                self.add(
                    "ERROR",
                    path,
                    0,
                    "invalid-mode",
                    "manifest mapping mode must be adapter, symlink, overlay, or dynamic",
                )
            wrapper_name = mapping.get("wrapper_name")
            if wrapper_name is not None and (
                not isinstance(wrapper_name, str) or not wrapper_name.strip()
            ):
                self.add(
                    "ERROR",
                    path,
                    0,
                    "invalid-wrapper-name",
                    "wrapper_name must be a non-empty string when provided",
                )
            if (
                not isinstance(wrapper, str)
                or not wrapper.strip()
                or not isinstance(source, str)
                or not source.strip()
                or not valid_mode
            ):
                continue

            wrapper_path = self._manifest_path(path, wrapper)
            if wrapper_path in wrappers:
                self.add("ERROR", path, 0, "duplicate-wrapper", "manifest wrappers must be unique")
            else:
                wrappers.add(wrapper_path)
            wrapper_target = self._resolve_manifest_target(
                path,
                wrapper,
                allowed_roots,
                "wrapper",
                allow_final_symlink=mode == "symlink",
            )
            source_target = self._resolve_manifest_target(
                path,
                source,
                allowed_roots,
                "source",
            )

            command_path_value = mapping.get("command_path")
            if isinstance(command_path_value, str) and command_path_value.strip():
                command_target = self._resolve_manifest_target(
                    path,
                    command_path_value,
                    allowed_roots,
                    "command",
                )
                if command_target:
                    edges[command_target[0]] = wrapper_path
            elif command_path_value is not None:
                self.add(
                    "ERROR",
                    path,
                    0,
                    "invalid-command-path",
                    "command_path must be a non-empty string",
                )

            source_path = self._manifest_path(path, source)
            edges[wrapper_path] = source_path
            if wrapper_target is None or source_target is None:
                continue
            self._validate_manifest_mode(
                path,
                mapping,
                mode,
                wrapper_target,
                source_target,
                source,
            )
        self._find_mapping_cycles(path, edges)
        self._validate_manifest_artifacts(path, data, allowed_roots)

    def _validate_manifest_artifacts(
        self,
        manifest: Path,
        data: dict[str, object],
        allowed_roots: list[Path],
    ) -> None:
        raw = data.get("artifacts", [])
        if not isinstance(raw, list):
            self.add("ERROR", manifest, 0, "invalid-artifacts", "manifest artifacts must be a list")
            return
        installed_seen: set[Path] = set()
        for artifact in raw:
            if not isinstance(artifact, dict):
                self.add("ERROR", manifest, 0, "invalid-artifact", "artifact entries must be objects")
                continue
            installed = artifact.get("installed")
            source = artifact.get("source")
            if not isinstance(installed, str) or not isinstance(source, str):
                self.add(
                    "ERROR",
                    manifest,
                    0,
                    "invalid-artifact",
                    "artifact requires installed and source path strings",
                )
                continue
            installed_path = self._manifest_path(manifest, installed)
            if installed_path in installed_seen:
                self.add(
                    "ERROR",
                    manifest,
                    0,
                    "duplicate-artifact",
                    "installed artifact paths must be unique",
                )
            installed_seen.add(installed_path)
            installed_target = self._resolve_manifest_target(
                manifest,
                installed,
                allowed_roots,
                "installed-artifact",
                allow_final_symlink=True,
            )
            source_target = self._resolve_manifest_target(
                manifest,
                source,
                allowed_roots,
                "artifact-source",
            )
            if installed_target and source_target and installed_target[1] != source_target[1]:
                self.add(
                    "ERROR",
                    manifest,
                    0,
                    "artifact-source-mismatch",
                    "installed artifact must resolve exactly to its declared source",
                )

    def _manifest_allowed_roots(self, path: Path, data: dict[str, object]) -> list[Path]:
        raw = data.get("allowed_roots")
        if not isinstance(raw, list) or not raw:
            self.add(
                "ERROR",
                path,
                0,
                "missing-allowed-roots",
                "manifest must define a non-empty allowed_roots list",
            )
            return []
        roots: list[Path] = []
        for value in raw:
            if not isinstance(value, str) or not value.strip():
                self.add(
                    "ERROR",
                    path,
                    0,
                    "invalid-allowed-root",
                    "allowed roots must be non-empty path strings",
                )
                continue
            candidate = self._manifest_path(path, value)
            # SECURITY-REVIEW: Allowed roots are untrusted manifest paths. They are
            # resolved only for containment checks and must identify directories.
            try:
                resolved = candidate.resolve(strict=True)
                if not resolved.is_dir():
                    raise NotADirectoryError
            except (OSError, RuntimeError):
                self.add(
                    "ERROR",
                    path,
                    0,
                    "invalid-allowed-root",
                    "allowed root is missing or is not a directory",
                )
                continue
            if resolved not in roots:
                roots.append(resolved)
        return sorted(roots, key=str)

    def _resolve_manifest_target(
        self,
        manifest: Path,
        value: str,
        allowed_roots: list[Path],
        role: str,
        *,
        allow_final_symlink: bool = False,
    ) -> tuple[Path, Path] | None:
        candidate = self._manifest_path(manifest, value)
        # SECURITY-REVIEW: Manifest target paths are untrusted. lstat classifies the
        # final entry without following it; resolved paths are constrained to an
        # allowlist before any bounded descriptor read.
        try:
            metadata = candidate.lstat()
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            self.add(
                "ERROR",
                manifest,
                0,
                f"missing-{role}-target",
                f"manifest {role} target is missing",
            )
            return None
        except (OSError, RuntimeError):
            self.add(
                "ERROR",
                manifest,
                0,
                f"invalid-{role}-target",
                f"manifest {role} target cannot be resolved",
            )
            return None
        if not any(resolved == root or resolved.is_relative_to(root) for root in allowed_roots):
            self.add(
                "ERROR",
                manifest,
                0,
                "target-outside-allowed-root",
                f"manifest {role} target resolves outside allowed_roots",
            )
            return None
        is_link = stat.S_ISLNK(metadata.st_mode)
        if is_link and not allow_final_symlink:
            self.add(
                "ERROR",
                manifest,
                0,
                "unexpected-symlink-target",
                f"manifest {role} target must not be a symlink",
            )
            return None
        if not is_link and not stat.S_ISREG(metadata.st_mode):
            self.add(
                "ERROR",
                manifest,
                0,
                "non-regular-target",
                f"manifest {role} target is not a regular file",
            )
            return None
        try:
            resolved_metadata = resolved.stat()
        except OSError:
            self.add(
                "ERROR",
                manifest,
                0,
                f"invalid-{role}-target",
                f"manifest {role} target cannot be inspected",
            )
            return None
        if not stat.S_ISREG(resolved_metadata.st_mode):
            self.add(
                "ERROR",
                manifest,
                0,
                "non-regular-target",
                f"manifest {role} target does not resolve to a regular file",
            )
            return None
        return candidate, resolved

    def _validate_manifest_mode(
        self,
        manifest: Path,
        mapping: dict[str, object],
        mode: str,
        wrapper_target: tuple[Path, Path],
        source_target: tuple[Path, Path],
        source_declaration: str,
    ) -> None:
        wrapper_path, wrapper_resolved = wrapper_target
        source_path, source_resolved = source_target
        wrapper_read_path = wrapper_resolved
        wrapper_text = self._read_text(wrapper_read_path)
        if wrapper_text is None:
            return
        wrapper_frontmatter, body_start = self._parse_frontmatter(
            wrapper_path,
            wrapper_text.splitlines(),
        )
        wrapper_name = wrapper_frontmatter.get("name", "")
        expected_name = mapping.get("wrapper_name")
        if not wrapper_name:
            self.add(
                "ERROR",
                manifest,
                0,
                "missing-wrapper-frontmatter-name",
                "wrapper SKILL frontmatter must define name",
            )
        if isinstance(expected_name, str) and wrapper_name != expected_name:
            self.add(
                "ERROR",
                manifest,
                0,
                "wrapper-name-mismatch",
                "wrapper SKILL name does not match wrapper_name",
            )

        expected_disable = mapping.get(
            "disable-model-invocation",
            mapping.get("disable_model_invocation"),
        )
        actual_disable = wrapper_frontmatter.get("disable-model-invocation")
        if expected_disable is not None and not isinstance(expected_disable, bool):
            self.add(
                "ERROR",
                manifest,
                0,
                "invalid-disable-contract",
                "manifest disable-model-invocation contract must be boolean",
            )
        elif isinstance(expected_disable, bool) and actual_disable != str(expected_disable).lower():
            self.add(
                "ERROR",
                manifest,
                0,
                "wrapper-disable-contract",
                "wrapper disable-model-invocation does not match the manifest contract",
            )
        wrapper_description = wrapper_frontmatter.get("description", "")
        wrapper_body = "\n".join(wrapper_text.splitlines()[body_start:])
        broad_authorization = bool(
            re.search(r"\b(?:broad|implicit)\s+authorization\b", wrapper_text, re.IGNORECASE)
        )
        mutating_wrapper = bool(MUTATION_RE.search(wrapper_body)) and (
            "loop" in f"{wrapper_name} {wrapper_description}".lower() or broad_authorization
        )
        if mutating_wrapper and actual_disable != "true":
            self.add(
                "ERROR",
                manifest,
                0,
                "mutating-wrapper-invocation",
                "mutating wrapper must set disable-model-invocation: true",
            )

        source_text: str | None = None
        if mode == "symlink":
            if wrapper_resolved != source_resolved:
                self.add(
                    "ERROR",
                    manifest,
                    0,
                    "symlink-source-mismatch",
                    "symlink installation must resolve exactly to the declared source file",
                )
        elif mode in {"adapter", "dynamic"} and source_declaration not in wrapper_text:
            self.add(
                "ERROR",
                manifest,
                0,
                f"{mode}-source-reference",
                f"{mode} wrapper must reference the declared source path",
            )

        if mode == "dynamic":
            if source_path.suffix.lower() != ".json":
                self.add(
                    "ERROR",
                    manifest,
                    0,
                    "dynamic-source-not-json",
                    "dynamic mode source must be a JSON metadata file",
                )
            source_text = self._read_text(source_resolved)
            if source_text is not None:
                try:
                    json.loads(source_text)
                except json.JSONDecodeError:
                    self.add(
                        "ERROR",
                        manifest,
                        0,
                        "invalid-dynamic-source",
                        "dynamic source is not valid JSON",
                    )
        else:
            source_text = self._read_text(source_resolved)
            if source_path.suffix.lower() == ".md":
                self._validate_manifest_markdown(source_resolved)

        if mode == "overlay" and source_text is not None:
            source_frontmatter, _ = self._parse_frontmatter(
                source_path,
                source_text.splitlines(),
            )
            if not wrapper_name or source_frontmatter.get("name") != wrapper_name:
                self.add(
                    "ERROR",
                    manifest,
                    0,
                    "overlay-name-mismatch",
                    "overlay wrapper and source SKILL names must match",
                )
            if wrapper_text != source_text:
                self.add(
                    "INFO",
                    manifest,
                    0,
                    "overlay-divergence",
                    "overlay wrapper content diverges from its declared source",
                )
        self._validate_manifest_markdown(wrapper_read_path)

    def _validate_manifest_markdown(self, path: Path) -> None:
        absolute = path.absolute()
        if absolute in self.checked_markdown or path.suffix.lower() != ".md":
            return
        self.checked_markdown.add(absolute)
        text = self._read_text(path)
        if text is None:
            return
        self._validate_links(path, text)
        self._validate_fences(path, text)
        self._validate_risky_patterns(path, text)
        self._validate_reviewer_counts(path, text)

    def _manifest_mappings(self, path: Path, data: object) -> list[object]:
        if not isinstance(data, dict):
            self.add("ERROR", path, 0, "invalid-manifest", "manifest must contain mappings")
            return []
        raw = data.get("mappings")
        if isinstance(raw, list):
            return raw
        self.add("ERROR", path, 0, "invalid-manifest", "manifest must define a mappings list")
        return []

    def _manifest_path(self, manifest: Path, value: str) -> Path:
        candidate = Path(os.path.expanduser(value))
        if not candidate.is_absolute():
            candidate = manifest.parent / candidate
        # SECURITY-REVIEW: Manifest paths are untrusted and normalized lexically
        # before allowlist validation; they are never executed.
        return Path(os.path.abspath(candidate))

    def _find_mapping_cycles(self, path: Path, edges: dict[Path, Path]) -> None:
        for start in sorted(edges, key=str):
            seen: set[Path] = set()
            current = start
            while current in edges:
                if current in seen:
                    self.add(
                        "ERROR",
                        path,
                        0,
                        "recursive-mapping",
                        "manifest contains a recursive wrapper/source mapping",
                    )
                    return
                seen.add(current)
                current = edges[current]

    def _read_text(self, path: Path) -> str | None:
        # SECURITY-REVIEW: Package paths are untrusted. lstat/O_NOFOLLOW/fstat
        # prevent final-entry symlink races and special-file hangs; reads are
        # descriptor-based, nonblocking, bounded, and never included in diagnostics.
        descriptor: int | None = None
        try:
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                self.add("ERROR", path, 0, "non-regular-file", "text path is not a regular file")
                return None
            flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(path, flags)
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                self.add("ERROR", path, 0, "non-regular-file", "opened text path is not regular")
                return None
            if (metadata.st_dev, metadata.st_ino) != (opened.st_dev, opened.st_ino):
                self.add("ERROR", path, 0, "changed-file", "text path changed while being opened")
                return None
            if opened.st_size > MAX_TEXT_BYTES:
                self.add("ERROR", path, 0, "file-too-large", "text file exceeds 2 MB validation limit")
                return None
            chunks: list[bytes] = []
            remaining = MAX_TEXT_BYTES + 1
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            if len(raw) > MAX_TEXT_BYTES:
                self.add("ERROR", path, 0, "file-too-large", "text file exceeds 2 MB validation limit")
                return None
            return raw.decode("utf-8")
        except (OSError, UnicodeError):
            self.add("ERROR", path, 0, "unreadable-text", "text file cannot be read as UTF-8")
            return None
        finally:
            if descriptor is not None:
                os.close(descriptor)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate one or more Claude skill package roots without following symlinks.",
        epilog=(
            'Manifest format: {"allowed_roots": ["path"], "mappings": '
            '[{"command": "name", "wrapper": "path", "source": "path", '
            '"mode": "adapter|symlink|overlay|dynamic"}]}. Use command_path '
            "for an installed command file target."
        ),
    )
    parser.add_argument("roots", nargs="+", type=Path, help="skill directory or parent root to scan")
    parser.add_argument(
        "--manifest",
        type=Path,
        help="JSON manifest with command/wrapper/source mappings",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        help="canonical loop contract that every scanned skill must package byte-for-byte",
    )
    return parser


def render(findings: Iterable[Finding], skill_count: int) -> str:
    ordered = sorted(findings)
    lines = []
    for finding in ordered:
        location = finding.path
        if finding.line:
            location = f"{location}:{finding.line}"
        lines.append(
            f"{finding.severity} {location} [{finding.code}] {finding.message}"
        )
    errors = sum(finding.severity == "ERROR" for finding in ordered)
    warnings = sum(finding.severity == "WARNING" for finding in ordered)
    infos = sum(finding.severity == "INFO" for finding in ordered)
    lines.append(
        f"SUMMARY skills={skill_count} errors={errors} warnings={warnings} info={infos}"
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validator = Validator(args.roots, args.manifest, args.contract)
    findings = validator.validate()
    print(render(findings, len(validator.skills)))
    return 1 if any(finding.severity == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())

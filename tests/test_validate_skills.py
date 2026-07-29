from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
assert SPEC and SPEC.loader
validate_skills = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_skills
SPEC.loader.exec_module(validate_skills)


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_skill(
        self,
        name: str = "safe-loop",
        *,
        frontmatter_name: str | None = None,
        body: str | None = None,
    ) -> Path:
        skill = self.root / name
        (skill / "references").mkdir(parents=True)
        (skill / "templates").mkdir()
        (skill / "references" / "guide.md").write_text(
            "# Guide\n\n```text\nexample\n```\n",
            encoding="utf-8",
        )
        if body is None:
            body = """# Safe loop

This mutating loop writes a result and documents PROJECT_NAME.
See the [guide](references/guide.md).

## Templates

- `{{PROJECT_NAME}}`: validated project name.

```bash
printf '%s\\n' "validated"
```
"""
        skill_name = frontmatter_name if frontmatter_name is not None else name
        (skill / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    f"name: {skill_name}",
                    "description: A mutating loop that writes local results.",
                    "disable-model-invocation: true",
                    "---",
                    "",
                    body.rstrip(),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (skill / "templates" / "output.md").write_text(
            "# {{PROJECT_NAME}}\n",
            encoding="utf-8",
        )
        return skill

    def write_skill_file(
        self,
        relative: str,
        name: str,
        body: str = "# Wrapper\n",
        *,
        disable: bool | None = None,
    ) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        frontmatter = [
            "---",
            f"name: {name}",
            "description: A local wrapper command.",
        ]
        if disable is not None:
            frontmatter.append(f"disable-model-invocation: {str(disable).lower()}")
        frontmatter.extend(["---", "", body.rstrip(), ""])
        path.write_text("\n".join(frontmatter), encoding="utf-8")
        return path

    def write_manifest(
        self,
        mappings: list[dict[str, object]],
        *,
        name: str = "manifest.json",
        allowed_roots: list[str] | None = None,
    ) -> Path:
        manifest = self.root / name
        manifest.write_text(
            json.dumps(
                {
                    "allowed_roots": allowed_roots or ["."],
                    "mappings": mappings,
                }
            ),
            encoding="utf-8",
        )
        return manifest

    def findings(self, *, manifest: Path | None = None) -> list[object]:
        validator = validate_skills.Validator([self.root], manifest)
        return validator.validate()

    def error_codes(self, *, manifest: Path | None = None) -> set[str]:
        return {
            finding.code
            for finding in self.findings(manifest=manifest)
            if finding.severity == "ERROR"
        }

    def test_valid_fixture(self) -> None:
        self.make_skill()

        self.assertEqual(set(), self.error_codes())

    def test_documented_placeholder_and_angle_metavariable_are_allowed(self) -> None:
        self.make_skill(
            body="""# Safe loop

Usage: `safe-loop <goal>`.

## Templates

- `{{PROJECT_NAME}}`: validated project name.
"""
        )

        self.assertEqual(set(), self.error_codes())

    def test_multiline_git_prohibition_is_allowed(self) -> None:
        self.make_skill(
            body="""# Safe loop

Do not
use `--no-verify`, force-push, or rewrite history.
"""
        )

        self.assertNotIn("unsafe-git-instruction", self.error_codes())

    def test_shared_contract_drift_is_rejected(self) -> None:
        skill = self.make_skill()
        contract = self.root / "contract.md"
        contract.write_text("# Contract\n", encoding="utf-8")
        (skill / "references" / "loop-contract.md").write_text(
            "# Drifted contract\n",
            encoding="utf-8",
        )
        validator = validate_skills.Validator([self.root], contract=contract)

        self.assertIn(
            "loop-contract-drift",
            {
                finding.code
                for finding in validator.validate()
                if finding.severity == "ERROR"
            },
        )

    def test_broken_relative_link(self) -> None:
        skill = self.make_skill()
        with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
            handle.write("\n[missing](references/missing.md)\n")

        self.assertIn("broken-relative-link", self.error_codes())

    def test_nested_self_symlink(self) -> None:
        skill = self.make_skill()
        os.symlink(skill, skill / skill.name)

        self.assertIn("nested-self-symlink", self.error_codes())

    def test_broken_symlink(self) -> None:
        skill = self.make_skill()
        os.symlink(skill / "missing", skill / "broken")

        self.assertIn("broken-symlink", self.error_codes())

    def test_frontmatter_name_must_match_directory(self) -> None:
        self.make_skill(frontmatter_name="different-name")

        self.assertIn("name-directory-mismatch", self.error_codes())

    def test_unsafe_workflow_patterns(self) -> None:
        self.make_skill(
            body="""# Unsafe workflow

Use origin/main and refs/branches/main.

```bash
git remote -v
git push --force
```

Set K=2-3 and policy.allow_implicit_invocation.
""",
        )

        self.assertTrue(
            {
                "origin-main",
                "branches-main",
                "bare-git-remote",
                "unsafe-git-instruction",
                "nondeterministic-k",
                "unsupported-policy",
            }.issubset(self.error_codes())
        )

    def test_manifest_missing_target(self) -> None:
        self.make_skill()
        wrapper = self.write_skill_file(
            "installed-command/SKILL.md",
            "installed-command",
            "Uses missing/SKILL.md.",
        )
        manifest = self.write_manifest(
            [
                {
                    "command": "safe-loop",
                    "wrapper": str(wrapper.relative_to(self.root)),
                    "source": "missing/SKILL.md",
                    "mode": "adapter",
                }
            ]
        )

        self.assertIn("missing-source-target", self.error_codes(manifest=manifest))

    def test_manifest_recursive_mapping(self) -> None:
        self.make_skill()
        first = self.write_skill_file("first/SKILL.md", "first", "Uses second/SKILL.md.")
        second = self.write_skill_file("second/SKILL.md", "second", "Uses first/SKILL.md.")
        manifest = self.write_manifest(
            [
                {
                    "command": "first",
                    "wrapper": str(first.relative_to(self.root)),
                    "source": str(second.relative_to(self.root)),
                    "mode": "adapter",
                },
                {
                    "command": "second",
                    "wrapper": str(second.relative_to(self.root)),
                    "source": str(first.relative_to(self.root)),
                    "mode": "adapter",
                },
            ]
        )

        self.assertIn("recursive-mapping", self.error_codes(manifest=manifest))

    def test_manifest_markdown_source_is_validated(self) -> None:
        self.make_skill()
        wrapper = self.write_skill_file(
            "wrapper/SKILL.md",
            "wrapper",
            "Loads command.md.",
        )
        source = self.root / "command.md"
        source.write_text("```bash\nif true; then\n```\n", encoding="utf-8")
        manifest = self.write_manifest(
            [
                {
                    "command": "command",
                    "wrapper": str(wrapper.relative_to(self.root)),
                    "source": source.name,
                    "mode": "adapter",
                }
            ]
        )

        self.assertIn("bash-syntax", self.error_codes(manifest=manifest))

    def test_manifest_modes(self) -> None:
        self.make_skill()

        adapter_source = self.write_skill_file(
            "sources/adapter-source/SKILL.md",
            "adapter-source",
        )
        adapter_wrapper = self.write_skill_file(
            "wrappers/adapter-wrapper/SKILL.md",
            "adapter-wrapper",
            "Loads sources/adapter-source/SKILL.md.",
        )
        adapter_manifest = self.write_manifest(
            [
                {
                    "command": "adapter",
                    "wrapper": str(adapter_wrapper.relative_to(self.root)),
                    "wrapper_name": "adapter-wrapper",
                    "source": str(adapter_source.relative_to(self.root)),
                    "mode": "adapter",
                }
            ],
            name="adapter.json",
        )

        symlink_source = self.write_skill_file(
            "sources/symlink-source/SKILL.md",
            "symlink-source",
        )
        symlink_wrapper = self.root / "wrappers/symlink-source/SKILL.md"
        symlink_wrapper.parent.mkdir(parents=True)
        os.symlink(symlink_source, symlink_wrapper)
        symlink_manifest = self.write_manifest(
            [
                {
                    "command": "symlink",
                    "wrapper": str(symlink_wrapper.relative_to(self.root)),
                    "wrapper_name": "symlink-source",
                    "source": str(symlink_source.relative_to(self.root)),
                    "mode": "symlink",
                }
            ],
            name="symlink.json",
        )

        overlay_source = self.write_skill_file(
            "sources/overlay/SKILL.md",
            "overlay",
            "# Source overlay\n",
        )
        overlay_wrapper = self.write_skill_file(
            "wrappers/overlay/SKILL.md",
            "overlay",
            "# Local overlay\n",
        )
        overlay_manifest = self.write_manifest(
            [
                {
                    "command": "overlay",
                    "wrapper": str(overlay_wrapper.relative_to(self.root)),
                    "wrapper_name": "overlay",
                    "source": str(overlay_source.relative_to(self.root)),
                    "mode": "overlay",
                }
            ],
            name="overlay.json",
        )

        dynamic_source = self.root / "metadata/dynamic.json"
        dynamic_source.parent.mkdir()
        dynamic_source.write_text('{"source": "local"}\n', encoding="utf-8")
        dynamic_wrapper = self.write_skill_file(
            "wrappers/dynamic-wrapper/SKILL.md",
            "dynamic-wrapper",
            "Loads metadata/dynamic.json.",
        )
        dynamic_manifest = self.write_manifest(
            [
                {
                    "command": "dynamic",
                    "wrapper": str(dynamic_wrapper.relative_to(self.root)),
                    "wrapper_name": "dynamic-wrapper",
                    "source": str(dynamic_source.relative_to(self.root)),
                    "mode": "dynamic",
                }
            ],
            name="dynamic.json",
        )

        for mode, manifest in (
            ("adapter", adapter_manifest),
            ("symlink", symlink_manifest),
            ("overlay", overlay_manifest),
            ("dynamic", dynamic_manifest),
        ):
            with self.subTest(mode=mode):
                findings = self.findings(manifest=manifest)
                self.assertEqual(
                    set(),
                    {finding.code for finding in findings if finding.severity == "ERROR"},
                )
        self.assertIn(
            "overlay-divergence",
            {finding.code for finding in self.findings(manifest=overlay_manifest)},
        )

    def test_duplicate_manifest_command_wrapper_and_mapping(self) -> None:
        self.make_skill()
        source_one = self.write_skill_file("sources/one/SKILL.md", "one")
        source_two = self.write_skill_file("sources/two/SKILL.md", "two")
        wrapper = self.write_skill_file(
            "wrappers/shared/SKILL.md",
            "shared",
            "Loads sources/one/SKILL.md and sources/two/SKILL.md.",
        )
        first = {
            "command": "same",
            "wrapper": str(wrapper.relative_to(self.root)),
            "source": str(source_one.relative_to(self.root)),
            "mode": "adapter",
        }
        second = {
            "command": "same",
            "wrapper": str(wrapper.relative_to(self.root)),
            "source": str(source_two.relative_to(self.root)),
            "mode": "adapter",
        }
        manifest = self.write_manifest([first, second, first])

        codes = self.error_codes(manifest=manifest)
        self.assertTrue(
            {"duplicate-command", "duplicate-wrapper", "duplicate-mapping"}.issubset(codes)
        )

    def test_adapter_rejects_unrelated_wrapper_and_wrong_source(self) -> None:
        self.make_skill()
        source = self.write_skill_file("sources/wrong/SKILL.md", "wrong")
        wrapper = self.write_skill_file(
            "wrappers/unrelated/SKILL.md",
            "unrelated",
            "Loads sources/right/SKILL.md.",
        )
        manifest = self.write_manifest(
            [
                {
                    "command": "unrelated",
                    "wrapper": str(wrapper.relative_to(self.root)),
                    "wrapper_name": "expected-wrapper",
                    "source": str(source.relative_to(self.root)),
                    "mode": "adapter",
                }
            ]
        )

        codes = self.error_codes(manifest=manifest)
        self.assertIn("adapter-source-reference", codes)
        self.assertIn("wrapper-name-mismatch", codes)

    def test_symlink_mode_rejects_wrong_source(self) -> None:
        self.make_skill()
        actual = self.write_skill_file("sources/actual/SKILL.md", "actual")
        declared = self.write_skill_file("sources/declared/SKILL.md", "declared")
        wrapper = self.root / "wrappers/actual/SKILL.md"
        wrapper.parent.mkdir(parents=True)
        os.symlink(actual, wrapper)
        manifest = self.write_manifest(
            [
                {
                    "command": "wrong-symlink",
                    "wrapper": str(wrapper.relative_to(self.root)),
                    "source": str(declared.relative_to(self.root)),
                    "mode": "symlink",
                }
            ]
        )

        self.assertIn("symlink-source-mismatch", self.error_codes(manifest=manifest))

    def test_manifest_rejects_special_file_without_hanging(self) -> None:
        self.make_skill()
        wrapper = self.write_skill_file(
            "wrappers/special/SKILL.md",
            "special",
            "Loads special.pipe.",
        )
        fifo = self.root / "special.pipe"
        os.mkfifo(fifo)
        manifest = self.write_manifest(
            [
                {
                    "command": "special",
                    "wrapper": str(wrapper.relative_to(self.root)),
                    "source": fifo.name,
                    "mode": "adapter",
                }
            ]
        )

        self.assertIn("non-regular-target", self.error_codes(manifest=manifest))

    def test_manifest_artifact_must_resolve_to_declared_source(self) -> None:
        self.make_skill()
        source = self.root / "runtime/source.py"
        other = self.root / "runtime/other.py"
        installed = self.root / "installed/runtime.py"
        source.parent.mkdir()
        installed.parent.mkdir()
        source.write_text("source\n", encoding="utf-8")
        other.write_text("other\n", encoding="utf-8")
        os.symlink(other, installed)
        manifest = self.write_manifest([])
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["artifacts"] = [
            {
                "installed": str(installed.relative_to(self.root)),
                "source": str(source.relative_to(self.root)),
            }
        ]
        manifest.write_text(json.dumps(data), encoding="utf-8")

        self.assertIn("artifact-source-mismatch", self.error_codes(manifest=manifest))

    def test_manifest_target_must_stay_beneath_allowed_root(self) -> None:
        self.make_skill()
        wrapper = self.write_skill_file(
            "allowed/wrapper/SKILL.md",
            "wrapper",
            "Loads outside/SKILL.md.",
        )
        source = self.write_skill_file("outside/SKILL.md", "outside")
        manifest = self.write_manifest(
            [
                {
                    "command": "escape",
                    "wrapper": str(wrapper.relative_to(self.root)),
                    "source": str(source.relative_to(self.root)),
                    "mode": "adapter",
                }
            ],
            allowed_roots=["allowed"],
        )

        self.assertIn("target-outside-allowed-root", self.error_codes(manifest=manifest))

    def test_parent_symlink_may_resolve_inside_allowed_root(self) -> None:
        self.make_skill()
        source = self.write_skill_file("allowed/source/SKILL.md", "source")
        wrapper = self.write_skill_file(
            "allowed/wrapper/SKILL.md",
            "wrapper",
            "Loads alias/source/SKILL.md.",
        )
        os.symlink(self.root / "allowed", self.root / "alias")
        manifest = self.write_manifest(
            [
                {
                    "command": "parent-symlink",
                    "wrapper": "alias/wrapper/SKILL.md",
                    "source": "alias/source/SKILL.md",
                    "mode": "adapter",
                }
            ],
            allowed_roots=["allowed"],
        )

        self.assertEqual(set(), self.error_codes(manifest=manifest))

    def test_mutating_wrapper_enforces_disable_contract(self) -> None:
        self.make_skill()
        source = self.write_skill_file("sources/action/SKILL.md", "action")
        wrapper = self.write_skill_file(
            "wrappers/action-loop/SKILL.md",
            "action-loop",
            "This loop writes files using sources/action/SKILL.md.",
            disable=False,
        )
        manifest = self.write_manifest(
            [
                {
                    "command": "action",
                    "wrapper": str(wrapper.relative_to(self.root)),
                    "source": str(source.relative_to(self.root)),
                    "mode": "adapter",
                    "disable-model-invocation": True,
                }
            ]
        )

        codes = self.error_codes(manifest=manifest)
        self.assertIn("wrapper-disable-contract", codes)
        self.assertIn("mutating-wrapper-invocation", codes)

    def test_package_link_escape_is_rejected_even_when_target_exists(self) -> None:
        skill = self.make_skill()
        (self.root / "outside.md").write_text("# Outside\n", encoding="utf-8")
        with (skill / "SKILL.md").open("a", encoding="utf-8") as handle:
            handle.write("\n[outside](../outside.md)\n")

        self.assertIn("package-link-escape", self.error_codes())

    def test_placeholder_colon_does_not_document_placeholder(self) -> None:
        self.make_skill(
            body="""# Safe loop

## Templates

- `{{PROJECT_NAME}}`: validated project name.

Owner: {{UNLISTED}}
""",
        )

        self.assertIn("placeholder-outside-template", self.error_codes())

    def test_unrelated_never_does_not_suppress_force_instruction(self) -> None:
        self.make_skill(
            body="""# Unsafe workflow

Never expose credentials.
Run `git push --force` when needed.
""",
        )

        self.assertIn("unsafe-git-instruction", self.error_codes())

    def test_bash_syntax_failure(self) -> None:
        self.make_skill(
            body="""# Invalid Bash

```bash
if true; then
  printf '%s\\n' "missing fi"
```
""",
        )

        self.assertIn("bash-syntax", self.error_codes())

    def test_cli_output_is_deterministic_and_nonzero(self) -> None:
        self.make_skill(frontmatter_name="wrong")
        first = io.StringIO()
        second = io.StringIO()

        with redirect_stdout(first):
            first_status = validate_skills.main([str(self.root)])
        with redirect_stdout(second):
            second_status = validate_skills.main([str(self.root)])

        self.assertEqual(1, first_status)
        self.assertEqual(first.getvalue(), second.getvalue())
        self.assertIn("SUMMARY skills=1", first.getvalue())


if __name__ == "__main__":
    unittest.main()

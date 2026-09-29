#!/usr/bin/env python3
"""Build the Codex copies in codex/skills/ from the canonical skills in skills/.

The Codex copy of a skill is the canonical folder plus two changes:
- SKILL.md drops the Claude-only `disable-model-invocation` line and gains a
  "Running in Codex" section right after its frontmatter;
- agents/openai.yaml sets `allow_implicit_invocation: false`, so Codex runs the
  skill only when it is mentioned as `$name`.

Run with --check to fail when codex/skills/ differs from a fresh build.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CODEX_NOTES = """\
## Running in Codex

This is the Codex copy of this skill. Read the rest of it with these translations:

- Agents launched in parallel: spawn each one with `spawn_agent` before waiting on any, then collect the
  results with `wait_agent`. Tell every agent you spawn not to spawn agents of its own. If subagents are
  unavailable, run each lane yourself, one after another.
- "Your default model" and "your strongest model": spawn the agent with an `agent_type` whose role file in
  `~/.codex/agents/` sets `model` and `model_reasoning_effort`. An agent without a role runs on the
  session's model.
- A slash command such as `/name`: mention the skill as `$name`.
- Claude Code hooks (Stop, SessionStart) and `.claude/` paths: Codex has neither. A loop runs one pass
  per invocation, saves its state and reports how to resume.
- `CLAUDE.md`: also read `AGENTS.md`, which is the file Codex loads.

"""

POLICY = "policy:\n  allow_implicit_invocation: false\n"


def codex_skill_md(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with frontmatter")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    front = [line for line in lines[1:end] if not line.startswith("disable-model-invocation:")]
    body = "".join(lines[end + 1 :]).lstrip("\n")
    return "---\n" + "".join(front) + "---\n\n" + CODEX_NOTES + body


def build(skills_root: Path, out_root: Path) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    for skill in sorted(p for p in skills_root.iterdir() if (p / "SKILL.md").is_file()):
        target = out_root / skill.name
        shutil.copytree(skill, target, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
        skill_md = target / "SKILL.md"
        skill_md.write_text(codex_skill_md(skill_md.read_text()))
        (target / "agents").mkdir(exist_ok=True)
        (target / "agents" / "openai.yaml").write_text(POLICY)


def differences(expected: Path, actual: Path) -> list[str]:
    found: list[str] = []

    def walk(cmp: filecmp.dircmp, prefix: str) -> None:
        found.extend(f"missing in codex/skills: {prefix}{n}" for n in cmp.left_only)
        found.extend(f"not built from skills/: {prefix}{n}" for n in cmp.right_only)
        found.extend(f"differs: {prefix}{n}" for n in cmp.diff_files + cmp.funny_files)
        for name, sub in cmp.subdirs.items():
            walk(sub, f"{prefix}{name}/")

    walk(filecmp.dircmp(expected, actual, ignore=["__pycache__"]), "")
    return found


def check(skills_root: Path, codex_root: Path) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "skills"
        build(skills_root, fresh)
        if not codex_root.is_dir():
            return [f"missing: {codex_root}"]
        # dircmp compares by stat signature first; force content comparison.
        filecmp.clear_cache()
        return sorted(
            set(differences(fresh, codex_root))
            | {
                f"differs: {p.relative_to(fresh)}"
                for p in fresh.rglob("*")
                if p.is_file()
                and (codex_root / p.relative_to(fresh)).is_file()
                and p.read_bytes() != (codex_root / p.relative_to(fresh)).read_bytes()
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if codex/skills/ is stale")
    args = parser.parse_args()
    skills_root, codex_root = REPO / "skills", REPO / "codex" / "skills"
    if args.check:
        problems = check(skills_root, codex_root)
        for problem in problems:
            print(problem)
        print("codex/skills is up to date" if not problems else "run: python3 scripts/build_codex.py")
        return 1 if problems else 0
    if codex_root.exists():
        shutil.rmtree(codex_root)
    build(skills_root, codex_root)
    print(f"built {codex_root.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

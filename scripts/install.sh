#!/usr/bin/env bash
# Link sstack skills (and optionally the sergio-loop hooks) into your home directory.
#
#   scripts/install.sh [--codex] [--hooks] [skill ...]
#
# With no skill names it links every skill. Claude Code skills go to ~/.claude/skills,
# Codex skills (--codex) to ~/.agents/skills. Anything already at a destination is moved
# into a timestamped backup folder first, so a repeated install never nests a link
# inside an old one. --hooks links the sergio-loop runtime into ~/.claude/hooks and prints
# the settings.json entries to add; it never edits settings.json.
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
stamp="$(date +%Y%m%d-%H%M%S)-$$"
codex=0
hooks=0
skills=()

usage() {
  sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while (($#)); do
  case "$1" in
    --codex) codex=1 ;;
    --hooks) hooks=1 ;;
    -h | --help) usage; exit 0 ;;
    -*) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) skills+=("$1") ;;
  esac
  shift
done

if ((codex)); then
  source_root="$repo/codex/skills"
  install_root="$HOME/.agents/skills"
  backup_root="$HOME/.agents/skills-backups/$stamp"
else
  source_root="$repo/skills"
  install_root="$HOME/.claude/skills"
  backup_root="$HOME/.claude/skills-backups/$stamp"
fi

# Move whatever sits at $1 into $2/<name>, then link $3 there.
link_into() {
  local destination="$1" backups="$2" source="$3"
  if [[ -e "$destination" || -L "$destination" ]]; then
    mkdir -p "$backups"
    mv "$destination" "$backups/"
    echo "moved aside: $destination -> $backups/$(basename "$destination")"
  fi
  ln -s "$source" "$destination"
  echo "linked: $destination -> $source"
}

mkdir -p "$install_root"
# If the install folder is the source folder (for example ~/.claude/skills is itself a link
# to this checkout), moving a "destination" aside would move the skill out of the repository.
if [[ "$(cd "$install_root" && pwd -P)" == "$(cd "$source_root" && pwd -P)" ]]; then
  echo "refusing: $install_root resolves to $source_root; nothing to link" >&2
  exit 1
fi

if ((${#skills[@]} == 0)); then
  for dir in "$source_root"/*/; do
    [[ -f "$dir/SKILL.md" ]] && skills+=("$(basename "$dir")")
  done
fi

for skill in "${skills[@]}"; do
  if [[ "$skill" == */* || ! -f "$source_root/$skill/SKILL.md" ]]; then
    echo "no such skill: $skill" >&2
    exit 1
  fi
  link_into "$install_root/$skill" "$backup_root" "$source_root/$skill"
done

if ((hooks)); then
  hook_root="$HOME/.claude/hooks"
  hook_backup_root="$HOME/.claude/hooks-backups/$stamp"
  mkdir -p "$hook_root"
  for file in sergio_loop_state.py sergio_loop_registration.py \
    sergio-loop-session-hook.py sergio-loop-stop-hook.py; do
    link_into "$hook_root/$file" "$hook_backup_root" "$repo/runtime/$file"
  done
  cat <<'JSON'

Merge these entries into ~/.claude/settings.json, keeping any hooks already there,
then open a fresh Claude Code session:

{
  "hooks": {
    "SessionStart": [
      {"matcher": "", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/sergio-loop-session-hook.py", "timeout": 10}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/sergio-loop-stop-hook.py", "timeout": 10}]}
    ]
  }
}
JSON
fi

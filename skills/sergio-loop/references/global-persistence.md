# Global Stop-hook persistence

The repository ships a dependency-free runtime in `runtime/`. Install all three files together under
`~/.claude/hooks/`; register `sergio-loop-session-hook.py` as a SessionStart hook and
`sergio-loop-stop-hook.py` as an additional global Stop hook.

The hook is inert unless the current repository contains an active
private global state for the nearest repository and exact SessionStart-exported session identity. Every
other session or inactive repository stops normally.

Start only after core state initialization succeeds:

```text
python3 ~/.claude/hooks/sergio_loop_state.py start --repo <CANONICAL_REPOSITORY> --session-id "$SERGIO_CLAUDE_SESSION_ID" --prompt-file <MODE_0600_PROMPT_FILE> --max-iter <STOP_CONTINUATION_LIMIT> --expires-in 21600
```

Claude Code permits at most eight consecutive Stop-hook blocks, so the stop continuation limit cannot
exceed `8`. Record the returned instance ID. Stop that exact session-bound instance on every terminal
outcome:

```text
python3 ~/.claude/hooks/sergio_loop_state.py stop --repo <CANONICAL_REPOSITORY> --session-id "$SERGIO_CLAUDE_SESSION_ID" --instance-id <RECORDED_INSTANCE_ID> --reason <TERMINAL_REASON>
```

Never edit runtime JSON directly or stack this hook with another continuation authority. The hook fails
open for missing, malformed, expired, mismatched, context-limit, token-limit, authentication, authorization,
OAuth, HTTP 401/403/429, and rate-limit conditions.

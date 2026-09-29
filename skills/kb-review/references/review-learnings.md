# Review learnings

What the team's reviewers flag, captured from real reviews so a PR can pass them the first time. `kb-review` reads this file first and cites an entry for every finding it bases on a learning.

Replace every `<...>` placeholder and delete the example rows you do not use. Rules for every entry:

- **One citation per learning,** to a place the reader can open: a PR review comment URL, a chat anchor, a call transcript line. A learning with no citation is an opinion; leave it out.
- **Dated.** Record when the reviewer last flagged it, so old habits can be told apart from current ones.
- **Superseded, not deleted.** When the team changes its mind, move the entry to the last section with the anchor that changed it.
- **Say how the reviewer phrased it** when the wording matters; paraphrase otherwise.

## Mining state

| field | value |
| --- | --- |
| last mined | `<YYYY-MM-DD>` |
| window covered | `<oldest PR or date>` to `<newest PR or date>` |
| sources mined | `<code host review comments, review-request chat threads, call notes>` |
| how to mine again | `<command or procedure, or "by hand">` |

`kb-review` judges freshness by "last mined", never by the file's modification time. Update this table only when new reviewer feedback was actually read.

## Quick checklist

Items that apply to almost every PR. Keep it short; each line cites where it came from.

- [ ] `<commit and PR title convention, for example conventional type and a length limit>` (`<citation>`)
- [ ] `<PR description sections the team expects, for example what, why, testing, references>` (`<citation>`)
- [ ] `<test or plan evidence tied to the exact head SHA>` (`<citation>`)
- [ ] `<lockfiles regenerated and committed for every platform>` (`<citation>`)
- [ ] `<no unused inputs, variables or options>` (`<citation>`)
- [ ] `<your item>` (`<citation>`)

## By job type

The main lens. It works whoever ends up reviewing.

| job type | what reviewers flag | citation | last seen |
| --- | --- | --- | --- |
| `<dependency bump>` | `<pin exact versions; changelog link in the body>` | `<PR comment URL>` | `<date>` |
| `<CI workflow>` | `<strict shell mode; secrets cleaned up even when the job fails>` | `<PR comment URL>` | `<date>` |
| `<infrastructure module>` | `<explain every non-empty plan line; imports must plan to no change>` | `<PR comment URL>` | `<date>` |
| `<access policy>` | `<no broad trust; unique policy names>` | `<chat anchor>` | `<date>` |
| `<your job type>` | `<what gets flagged>` | `<citation>` | `<date>` |

## By reviewer (optional overlay)

Use only when you know who will review. Name reviewers by handle, and only if the team is fine with this file holding per-person notes.

### `<reviewer-handle>`

- Flags: `<the things this reviewer reliably raises>` (`<citation>`)
- How they review: `<depth, tone, what they read first, what they approve without comment>` (`<citation>`)
- Last reviewed a team PR: `<date>`

### `<another-reviewer-handle>`

- Flags: `<...>` (`<citation>`)
- How they review: `<...>` (`<citation>`)
- Last reviewed a team PR: `<date>`

## Recurring findings

Findings that came back on several PRs. The count shows where a checklist item or a lint rule would pay off.

| finding | times seen | citations | status |
| --- | --- | --- | --- |
| `<a script without strict error handling>` | `<3>` | `<URL>`, `<URL>`, `<URL>` | `<active>` |
| `<your finding>` | `<n>` | `<citations>` | `<active or superseded>` |

## Do not flag

Things that look wrong but are the agreed pattern. Lanes receive this list so they stop re-raising settled points.

| looks like | why it is fine | citation |
| --- | --- | --- |
| `<a pattern that looks wrong>` | `<the decision behind it>` | `<call or chat anchor>` |

## Canonical precedents

The PRs the team points to as "do it like this".

| change type | reference PR | what to copy |
| --- | --- | --- |
| `<migration of a service to a shared module>` | `<PR URL>` | `<layout, description shape, plan evidence>` |

## Routing precedents

Requests that belong to another team, and where they went.

| kind of request | owner | where to route |
| --- | --- | --- |
| `<build pipeline authentication>` | `<owning team>` | `<their channel or queue>` |

## Superseded learnings

| learning | was cited by | superseded by | date |
| --- | --- | --- | --- |
| `<old rule>` | `<citation>` | `<citation of the change>` | `<date>` |

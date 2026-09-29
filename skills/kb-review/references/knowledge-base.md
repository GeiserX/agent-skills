# Knowledge-base adapter

Fill this file in once for your team. The research and review skills read it first and follow it exactly. It is the only place that knows where your record lives and how to query it.

Replace every `<...>` placeholder and delete the example rows and sections you do not use. Keep secrets out: name the environment variable or keychain entry that holds a token, never the token. The same file serves `kb-research` and `kb-review`; keep one copy and symlink or copy it into the other. When a trap bites, add it to section 9 so it cannot bite twice.

## 1. Sources, ranked by authority

| rank | source | kind | authoritative for | query recipe |
| --- | --- | --- | --- | --- |
| 1 | `<decision log or ADR folder>` | markdown folder | what was decided | 3a |
| 2 | `<call transcripts>` | FTS index | the reasons behind a decision | 3b |
| 3 | `<chat archive>` | SQLite database | who said what, when | 3b |
| 4 | `<ticket tracker>` | CLI or API | scope, acceptance criteria, status | 3e |
| 5 | `<wiki>` | RAG endpoint or MCP tool | runbooks, designs | 3c or 3d |
| 6 | `<code host>` | CLI or API | pull requests, review comments, current code | 3e |

When two sources disagree, the higher rank wins unless the lower one is newer and explicitly reverses it. Out of reach on purpose: `<sources the skills must not use, and why>`.

## 2. Access preconditions

For each source that needs a network, a login or a running app, give a bounded probe and what "up" looks like. Test reachability, not process state: any real HTTP code means the route is up, `000` means no route. If a probe fails, the skill stops and asks the user. It never proceeds on stale local data without saying so.

```bash
URL='<https://an-internal-host-behind-your-vpn>'
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 6 "$URL")
if [ "$code" = "000" ]; then echo "access: DOWN, ask the user to connect <your VPN>"; else echo "access: ok ($code)"; fi
```

Per source: `<source>`: probe `<command>`, up means `<expected output>`, if down tell the user `<what to connect or re-authenticate>`.

## 3. How to query each source

For each recipe, record what an empty result looks like and what an error looks like. They must be distinguishable.

### 3a. Markdown or text folder (ripgrep)

```bash
KB_DIR='<path to your markdown folder>'
QUERY='<rare token>'
rg -n -i --no-heading -C 2 -- "$QUERY" "$KB_DIR"
rg -q -i -- "$QUERY" "$KB_DIR"; echo "rg exit: $?"   # 1 = no match, 2 = error; both print nothing
```

### 3b. SQLite full-text index (FTS5)

```bash
DB='<path to your index.sqlite>'
# QUERY is an FTS5 expression. Put any term with a character other than a letter, digit or underscore
# in double quotes, as in "O'Reilly" or "retry-budget"; bare, FTS5 rejects it with an error.
QUERY='<rare token> OR "<exact phrase>"'
SAFE=${QUERY//\'/\'\'}   # double single quotes so the query cannot break out of the SQL string
sqlite3 -readonly "$DB" "SELECT path, snippet(docs, 1, '[', ']', ' ... ', 12) FROM docs WHERE docs MATCH '$SAFE' ORDER BY rank LIMIT 20;"
```

Table and columns: `<table, text, date, author>`. Open with `-readonly` when another process writes to the file.

### 3c. RAG or vector endpoint (curl or a script)

```bash
RAG_URL='<https://your-rag-endpoint/search>'
QUERY="<question in the record's own words>"
jq -n --arg query "$QUERY" '{query: $query, top_k: 10}' |
  curl -sS --max-time 30 -H "Authorization: Bearer $RAG_TOKEN" -H 'Content-Type: application/json' \
    --data-binary @- "$RAG_URL"
```

Response fields: `<field with the text>`, `<field with the source path or URL>`, `<field with the date>`. A vector search always returns its top k, even when nothing is relevant, so a hit is a lead until you open the source it names.

### 3d. MCP tool

```text
tool: <server name>.<tool name>
arguments: {"query": "<rare token>", "limit": 20}
result: <where the hits are in the response, and the field that holds the anchor>
error: <how a failed call looks, for example ok:false with an error field>
```

### 3e. CLI or wiki or ticket API

```bash
CLI='<your-cli>'
"$CLI" search '<query>' --limit 20 --json
```

Filters: `<date flag>`, `<author flag>`, `<project or space flag>`. Paging: `<how to fetch the next page>`.

## 4. How to cite

| source | anchor format | example | verify a quote by |
| --- | --- | --- | --- |
| markdown | `path:line` | `<decisions/0012-caching.md:40>` | reading the line |
| transcript | `file:line` or `file@hh:mm` | `<calls/2026-03-02.txt:L120>` | reading the raw transcript, not the summary |
| chat | `[date #channel] permalink` | `<[2026-03-02 #design] https://...>` | opening the thread |
| ticket | key and URL | `<KEY-123 https://...>` | fetching the ticket |
| PDF or document | `file#page=N` | `<contract.pdf#page=4>` | extracting that page |

## 5. Freshness and refresh

| source | typical lag | freshness check | refresh (optional) | lock for the refresh |
| --- | --- | --- | --- | --- |
| `<source>` | `<for example up to 1 hour>` | `<command that prints the newest complete day>` | `<command, or none>` | `<lock path, or none>` |

- Live source for today: `<where messages newer than the index can be read>`.
- Staleness horizon for decisions: `<for example 90 days>`. Older decisions are flagged for re-confirmation.
- Content not searchable as text: `<images, screen shares, attachments>`. How to count it: `<command>`.

## 6. Routing by question type

| question type | primary sources | skip |
| --- | --- | --- |
| what was decided about X | `<decision log, transcripts>` | `<wiki drafts>` |
| who owns X | `<service catalog, ticket tracker>` | `<old chat>` |
| did we already decide this | `<decision log, transcripts, chat>` | |

## 7. Vocabulary

| canonical term | other spellings and mis-hearings | old names (period used) |
| --- | --- | --- |
| `<term>` | `<spellings>` | `<old name> (until <date>)` |

People: `<how names appear in each source, for example "Last, First" in chat and a login on the code host>`. Match names with a substring or LIKE, never with equality.

## 8. Measured search quality (optional)

Keep a small gold set of questions with known answers and re-measure after big changes to the index.

| query mode | recall at 5 | measured on | use it for |
| --- | --- | --- | --- |
| `<mode>` | `<0.00>` | `<date, gold set size>` | `<targeting, topic surveys>` |

## 9. Known traps

- A search tool returns nothing with exit status 0. Run a positive control before trusting an empty result.
- An API error looks like zero results (an HTTP 4xx with an empty list, or ok:false inside a success). Check the status and the error field first.
- Search ranks by relevance, not date. Sort by date before reading hits as a timeline.
- The archive stores one copy of a message per fetch. Group by message id or every count is wrong.
- Stored text keeps markup (bold markers, link syntax, mentions), so an exact phrase can miss. Search single words.
- Case-insensitive matching may not ignore accents. Search a stem or use a wildcard.
- Bot and automation accounts can carry a person's display name. Never attribute their lines to that person.
- A refused connection to a local app means the app is closed. Say so and answer without it.
- `<your trap: what happened, how to detect it, what to do instead>`

## 10. Privacy rules

- Never quote outward: `<private chats, personal data, credentials, customer data, anything marked confidential>`.
- Answers may go to: `<the user only | the team channel | public>`. Anything leaving that boundary is paraphrased and stripped of names.
- Redact before output: `<patterns such as tokens, emails, internal hostnames>`.

## 11. Findings cache (optional)

Location: `<path or none>`. Each entry holds a topic in the record's own words, a one-sentence finding, its anchors, and the date stored. An entry is stale when the record discussed the topic after that date. Only the user, or a refresh step marked safe in section 5, writes to it.

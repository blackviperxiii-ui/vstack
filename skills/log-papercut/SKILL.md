---
name: log-papercut
description: "Append one structured JSONL papercut when a tool, script, or skill fails unexpectedly or burns more than 2 retries. Shared queue for friction, tool bugs, and skill gaps. Use for /log-papercut, silent retry loops, or missing skill guidance."
---

# Log Papercut

Record friction once, then change approach. Do not silently retry the same failing path.

Always-on from **viper-mode**: unexpected tool/script/skill failure, or the same approach burns more than 2 retries. Skip expected, already-handled misses (create a missing file, fix a red lint).

Adapted from Uber Engineering's agent skills playbook (friction queue idea only; no large verbatim copy).

## Schema (one JSON object per line)

Required fields on every entry:

| Field | Type | Meaning |
|---|---|---|
| `timestamp` | string | ISO-8601 UTC (`date -u +%Y-%m-%dT%H:%M:%SZ`) |
| `source` | string | `skill`, `tool`, or `repo` |
| `tried` | string | What you ran or followed |
| `expected` | string | What should have happened |
| `observed` | string | What actually happened (error class / outcome, not a dump) |
| `suggested_fix` | string | Concrete next fix for a human or later agent |
| `turns_spent` | number | Integer turns burned on this friction |

**Hard rule: no secrets**, credentials, tokens, API keys, personal info, real emails, usernames in home paths, or raw env dumps. Redact values to `<redacted>`. Prefer `/home/user` over a real home path.

Append-only. Never edit or delete prior lines.

## 1. Resolve the queue path

Use the first match:

1. `$VSTACK_PAPERCUTS_PATH` when set and non-empty.
2. `<git-root>/.vstack/papercuts.jsonl` when `git rev-parse --show-toplevel` succeeds and that root has a `.vstack/` directory (repo opt-in).
3. Otherwise `~/.vstack/papercuts.jsonl` (create `~/.vstack` if needed).

```bash
if [ -n "${VSTACK_PAPERCUTS_PATH:-}" ]; then
  QUEUE="$VSTACK_PAPERCUTS_PATH"
elif ROOT=$(git rev-parse --show-toplevel 2>/dev/null) && [ -d "$ROOT/.vstack" ]; then
  QUEUE="$ROOT/.vstack/papercuts.jsonl"
else
  QUEUE="${HOME}/.vstack/papercuts.jsonl"
fi
echo "QUEUE=$QUEUE"
mkdir -p "$(dirname "$QUEUE")"
```

Verify: `test -d "$(dirname "$QUEUE")"` and reprint `QUEUE=...`.

Do not create `<git-root>/.vstack/` yourself. That directory is the opt-in signal.

## 2. Build one entry

Fill every field. Keep each string one short line. Count only turns spent on this friction in `turns_spent`.

```bash
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# Set SOURCE, TRIED, EXPECTED, OBSERVED, FIX, TURNS for this papercut.
python3 - <<'PY' > /tmp/papercut-entry.json
import json, os
entry = {
    "timestamp": os.environ["TS"],
    "source": os.environ["SOURCE"],       # skill | tool | repo
    "tried": os.environ["TRIED"],
    "expected": os.environ["EXPECTED"],
    "observed": os.environ["OBSERVED"],
    "suggested_fix": os.environ["FIX"],
    "turns_spent": int(os.environ["TURNS"]),
}
print(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))
PY
```

Export the fields into the environment before that block (`export TS SOURCE TRIED EXPECTED OBSERVED FIX TURNS`).

Verify the draft parses and has every key:

```bash
python3 - <<'PY'
import json
from pathlib import Path
required = {"timestamp","source","tried","expected","observed","suggested_fix","turns_spent"}
obj = json.loads(Path("/tmp/papercut-entry.json").read_text(encoding="utf-8"))
missing = required - set(obj)
assert not missing, f"missing {missing}"
assert obj["source"] in {"skill","tool","repo"}, obj["source"]
assert isinstance(obj["turns_spent"], int) and obj["turns_spent"] >= 0
print("draft OK")
PY
```

## 3. Append and verify

```bash
cat /tmp/papercut-entry.json >> "$QUEUE"
python3 - <<'PY'
import json, os
from pathlib import Path
queue = Path(os.environ["QUEUE"])
line = queue.read_text(encoding="utf-8").splitlines()[-1]
obj = json.loads(line)
print("appended", obj["timestamp"], obj["source"], "turns=", obj["turns_spent"])
PY
```

Verify: the last printed line shows `appended` with your `timestamp` and `source`. Then change approach (different tool, different skill, escalate). Do not retry the same failing path.

## Error recovery

| Failure | Recovery |
|---|---|
| `dirname` missing / `mkdir` fails on home path | Set `QUEUE=/tmp/vstack-papercuts.jsonl`, `mkdir -p /tmp`, append there, and say the fallback path in the reply. |
| Permission denied writing `$QUEUE` | Same fallback to `/tmp/vstack-papercuts.jsonl`. Do not rewrite or truncate the original file. |
| `git rev-parse` fails outside a repo | Use `~/.vstack/papercuts.jsonl` (step 1 branch 3). Do not invent a repo-local path. |
| Draft JSON fails the verify script | Fix the draft fields; do not append until `draft OK`. |
| Last line of `$QUEUE` is not valid JSON after append | Print that line with `tail -n 1 "$QUEUE"`. Leave prior lines untouched. Append a corrected entry as a new line only. |
| Entry would need a secret to describe the failure | Write the error *class* (`auth_rejected`, `missing_env:API_TOKEN`) and `<redacted>` for values. If you cannot describe it safely, skip the append and escalate in the reply instead. |

## Checklist

- [ ] Trigger was unexpected failure or >2 retries on the same approach.
- [ ] Path resolved via `$VSTACK_PAPERCUTS_PATH`, repo `.vstack/`, or `~/.vstack/papercuts.jsonl`.
- [ ] Every schema field present; no secrets or personal info.
- [ ] Last queue line parses as JSON.
- [ ] Approach changed after the log (no silent retry loop).

---
name: why
description: Why does X work this way? Design rationale, regressions, postmortems, where a number came from. Cited read across every evidence source. Use how for runtime. /why.
---

# Why

Answer from the record, not just the code: commits and PRs that introduced the target and later changes, plus other sources when thin. Cite authors, mark inferences, say what the record does not answer.

## 1. Target and question

Target = code, pattern, feature, or decision. Vague? Guess from context (open files, recent edits), state it, proceed.

## 2. Code anchor (inline, before spawning)

Paths + line ranges, key symbols, `git blame -L`, `git log --follow -p`, `git log --oneline -20`, PR numbers from subjects `(#123)`, then PR bodies, reviews, linked tickets (`gh pr view`). Every investigator gets this anchor.

## 3. Investigators (parallel, one source each)

List MCPs; one investigator per category with a source: source control (always), issue tracker, long-form docs, team chat, observability, error tracking, analytics warehouse. Agent mode, not readonly (readonly strips MCP); write nothing. Model per `vstack-models.mdc` `why` line (default `auto`). Defensive code → also hunt incidents and postmortems.

Skip a category only in writing: no MCP (a gap), or irrelevant. Answer inline only when the PR already holds the full answer and you say so. Nulls are findings.

## 4. Synthesize

One synthesizer: findings, nulls, skips, anchor, question.

- **Found** — cited fact (commit, PR, ticket, message).
- **Inferred** — reasoned from facts; say from which.
- **Competing hypotheses** — when evidence splits.
- **Unknown** — what no source answered.

## Output

The Question, The Code, What We Found, What We Can Infer, Competing Hypotheses, What We Don't Know, Sources Consulted (one line per category, empty/skipped with reason), Confidence Summary. Keep confidence language. Before a change, end with Preserve / Change / Avoid / Risk.

Avoid recency bias: the latest commit is rarely the whole story. Trace back.

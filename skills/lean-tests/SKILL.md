---
name: lean-tests
description: "Make a test suite and its CI jobs faster without losing coverage: measure first, push proof down the ladder, keep budgets, change one round at a time, report before/after. Use for /lean-tests, 'tests are slow', 'suite too slow for CI', 'push tests down', or speeding a file/class/branch's tests."
---

# Lean Tests

Make the suite and its CI jobs faster while every behavior still has a faster (or same) proof. Workflow layout, caches and job staging belong to **lean-ci**. App runtime cost belongs to **optimize**.

Adapted from Marek Kirejczyk's MIT [refactor-tests](https://github.com/marekkirejczyk/skills/tree/main/skills/refactor-tests) skill; method summarized here in vstack style.

Cite **viper-mode**, **principle-prove-it-works**, **principle-explain-the-number**, **principle-sequence-verifiable-units**, **principle-laziness-protocol**.

## Hard rules

These hold even when the user says "just make it fast":

- Never delete or loosen a test or an assertion to buy speed.
- Never add a skipped test. A behavior bug goes in a findings log; leave today's behavior pinned by a green test.
- CI job and step timeouts stay as they are.
- Every test you remove names the faster test that proves the same thing (write that test first if it is missing).

## 1. Measure first

Baseline on a **clean checkout of the base commit**, on a quiet machine, before touching any test.

**CI jobs.** Split wall time per step into: setup, compile/build, test run, smoke/e2e. Record the run id for each measured run.

**Local suites.** Prefer CPU time (`user` + `sys` from `/usr/bin/time -p`), not wall time alone: wall time hides parallel work on many cores.

Example commands (pick what the repo uses):

```bash
# Rust: nextest CI profile + JUnit timings
cargo nextest run --profile ci --message-format junit > /tmp/junit.xml
# or: CARGO_TERM_PROGRESS_WHEN=never cargo nextest run --profile ci

# Rust: stock cargo test under time
/usr/bin/time -p cargo test

# JS/TS: vitest or npm script under time
/usr/bin/time -p npx vitest run
/usr/bin/time -p npm test
```

Write down suite CPU time, test count, and the slowest files/tests. That table is the before column.

## 2. Push-down ladder

Keep each test at the **fastest level that can prove what it asserts**. Ladder, fastest first:

1. Pure function
2. Unit / service (fakes ok when they still prove the outcome)
3. Integration / route (real wiring, DB, or HTTP boundary)
4. App smoke / browser (one journey per critical flow, or what needs a real browser)

For each slow test in scope, write a one-line **verdict** in working notes:

- **stays** — only this level can prove it (name what)
- **moves** — to which faster level
- **covered-by** — name the faster test that already proves every assertion

Move or drop only after proof: break the behavior briefly, confirm a remaining test goes red, revert the break. No red remaining test → verdict is **stays**.

## 3. Budgets

Put each cost at the highest level that can carry it:

| Level | Paid | What belongs here |
| --- | --- | --- |
| **Run** | Once per suite invocation | Compiles, migrations once, shared fixtures/snapshots |
| **File** | Once per test file / module setup | Importing the app, starting services for that file |
| **Test** | Every test, including its own setup | One call, one request, one round trip |

Before splitting a test or giving each example fresh state, **price the split**: new test count × setup cost per test. If that product breaks a budget, cheapen setup first (snapshot, template, shared read-only fixture), then split.

## 4. Rounds

One change per round. Re-run the suite (or the scoped package) and stay green before the next round. Red after a round means the round changed behavior: undo it and take a smaller step.

Fix order when something is over budget:

1. Prepare once per run and copy per test.
2. Replace a real dependency with a fake where the level still proves the claim.
3. Share expensive read-only fixtures across a file last, and say so in the report.

## 5. Report: `## Test speed`

Put this section in the PR body (replace it if it already exists):

- Before and after **per CI job and per step** (setup, compile/build, test run, smoke/e2e), with **measured run ids**.
- Suite CPU time and test count, before and after (local).
- Each test moved or removed, and the faster test that now covers it.
- What is still over budget, its time, and the named cause.

Stop when budgets hold or every remaining over-budget item has a cause and a next fix (Laziness Protocol). Hand contested numbers to **benchmark-checklist**. Hand CI workflow changes to **lean-ci**.

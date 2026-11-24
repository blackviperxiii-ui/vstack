---
name: arena
description: Race N candidates at one design, pick a base, graft the best of the rest. Large or contested designs. /arena.
disable-model-invocation: true
---

# Arena

Only for a large or contested design, or on ask. Todo: Frame, Fan out, Judge, Pick, Graft, Verify.

**Frame.** Name the artifact. Rubric: 3-6 gradeable criteria, hidden from candidates. Runners per `vstack-models.mdc` `arena` line (default `auto`: 2-3 parent-model seats, one design direction each); other models only on high-stakes ask. Rejected slug: nearest in family or drop; keep two. Own worktree or temp dir per candidate.

**Fan out** in one message, background. Brief: task, grounding path, output path; return artifact plus rationale naming rejected alternatives. Dropout: continue, note it.

**Judge.** One fresh read-only judge scores candidates per criterion and recommends a base. Multi-model: judge from a vendor other than the parent's.

**Pick.** Read every candidate fully; score per criterion, not feel. Judge disagrees: read both rationales. Base: easiest to extend without breaking invariants; tie → smaller API.

**Graft.** One or two things per loser, folded in by hand under one mental model (**principle-redesign-from-first-principles**). Convergence: ship it, no graft. Wild divergence: reframe and rerun, don't average.

**Verify** (**principle-prove-it-works**). A miss: wrong Frame (rerun) or missed graft.

**Output:** artifact plus note: base and why, judge verdict, grafts with source, rejections, dropouts, verification.

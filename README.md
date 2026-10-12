# vstack — Viper Stack

Token-efficient adaptation of [poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack) skills for Cursor.

Keeps **all the rigor and value** of the original playbooks, principles, verification, how/why, etc., while defaulting to Auto mode or Composer 2.5 Standard so limited token allowances last longer.

## Why

Original pstack defaults lean hard into expensive models (e.g. grok-4.7-xhigh-fast). This config overrides that via the official model rule mechanism so subagents inherit the parent chat model.

## Quick Start

1. In a Cursor chat:
   ```
   /add-plugin pstack
   ```

2. Copy the contents of [`pstack-models.mdc`](./pstack-models.mdc) into `~/.cursor/rules/pstack-models.mdc` on your machine.

   Or run `/setup-pstack` and choose **auto** for every role + **medium** or **small** budget.

3. In the model picker, set your main chat to:
   - **Auto** (Cost or Balance recommended for limited tokens), **or**
   - **Composer 2.5** with Fast turned **OFF** (Standard tier).

4. Start a fresh chat so the rule loads, then use `/poteto-mode` as usual.

## The Config

See [`pstack-models.mdc`](./pstack-models.mdc).

It sets almost every role to `auto` (or `inherit-parent`), which omits the explicit model on Task subagents so they follow the parent. Panels are single-entry to avoid multi-model token multipliers while still getting the verification value of the playbooks.

Budget is set to medium (high). Change the comment to `small` if you want even lower spend.

## Why This Still Preserves Full Value

- All 23 playbooks and principles (laziness protocol, guard-the-context-window, prove-it-works, sequence-verifiable-units, etc.) remain unchanged.
- You still get rigorous, evidence-based engineering work.
- Existing efficiency principles are amplified because expensive model defaults no longer fight them.
- Composer 2.5 Standard and Auto share the cheaper Cursor Models pool.

## Extra Tips

- Only invoke `/poteto-mode` for non-trivial work.
- Prefer sequential verification over large parallel panels unless high-stakes.
- Strongly follow Guard the Context Window and Laziness Protocol.
- If you need an explicit pin, a custom agent with `model: composer-2.5[fast=false]` is more reliable than inline Task model parameters.

## Credits

Original pstack by Lauren Tan (@poteto). This is a lightweight config overlay for personal/token-conscious use. MIT license on upstream.

---

Made for Viper. 🐍
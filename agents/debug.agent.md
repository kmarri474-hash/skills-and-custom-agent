---
name: debug
description: Systematically reproduce, isolate, and fix a bug, then guard it with a regression test. A tight diagnosis loop — no guess-and-check.
tools: ['edit', 'search/codebase', 'search/usages', 'read/problems', 'execute/runInTerminal', 'execute/getTerminalOutput', 'execute/runTests', 'execute/testFailure', 'web/fetch']
---

# Debug

Drive a bug to a verified fix through one disciplined loop. A bug you can't reproduce isn't understood yet — earn the fix by making the failure visible first, never by guessing.

## The loop

1. **Reproduce.** Run the app or tests until the failure happens on demand. Pin the exact trigger, the expected behaviour, and the actual behaviour. Can't reproduce it? Stop and gather more signal — do not fix blind.
2. **Minimise.** Strip the reproduction to the smallest input and code path that still fails. A small red case localises the cause.
3. **Hypothesise.** From the minimal case, name the most likely cause and the evidence that would confirm it. Check git history for the change that introduced it.
4. **Instrument.** Make the cause observable — a log, a breakpoint, a failing assertion — and confirm the hypothesis *before* touching the fix. If the evidence doesn't land, re-hypothesise.
5. **Fix.** Make the smallest change that removes the confirmed cause, in the codebase's existing style. Resist refactoring around it.
6. **Regression-test.** Add a test that goes red without the fix and green with it, then run the broader suite to prove nothing else broke.

## Report

Close with the root cause in a sentence or two, the fix, the regression test guarding it, and any nearby code likely to carry the same bug.

**Done when** the original reproduction passes, the new regression test guards it, and the full suite is green.

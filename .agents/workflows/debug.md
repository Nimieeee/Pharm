---
description: Structured guide for deep debugging sessions using Pollinations AI (Kimi-optimized)
---

# 🕵️ Systematic Debugging Workflow

Use this workflow when you encounter bugs, test failures, or unexpected behavior. This workflow is optimized for the `kimi` (Debugger/Reader) model on Pollinations AI.

## 🚀 The Process

### Phase 1: Root Cause Investigation
**Stop!** Do not propose any fixes yet.
1. **Gather Evidence**: Run the code and capture exact error messages and stack traces.
2. **Reproduce**: Confirm you can trigger the bug reliably.
3. **Trace Data Flow**: Trace the bad values from where they are detected back to their origin.
4. **Log State**: Add diagnostic logging at component boundaries to isolate the failure.

### Phase 2: Hypothesis & Minimal Testing
1. **Form Hypothesis**: "I think X is the root cause because Y."
2. **Test Minimally**: Make the smallest possible change to verify your hypothesis.
3. **Validate**: Did the change explain the behavior? If not, revert and form a new hypothesis.

### Phase 3: The Fix
1. **Create Failing Test**: Use [TDD](file:///Users/mac/claude-code-proxy/.agents/skills/test-driven-development/SKILL.md) to define the bug and prevent regressions.
2. **Implement Root Cause Fix**: Address the source of the problem, not just the symptom.
3. **Verify**: Run ALL tests to ensure no new regressions were introduced.

## 🚩 Red Flags
- "Let's just try this..."
- Proposing fixes before seeing a stack trace.
- Bundling refactoring with a bug fix.

> [!TIP]
> Use the [systematic-debugging](file:///Users/mac/claude-code-proxy/.agents/skills/systematic-debugging/SKILL.md) skill for detailed checklists at each phase.

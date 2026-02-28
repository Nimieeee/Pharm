---
description: Structured guide for architecting and planning new features (GLM-optimized)
---

# 🏗️ Feature Architecting & Planning Workflow

Use this workflow before starting any new feature or major refactor. This workflow is optimized for the `glm` (Architect/Planner) model on Pollinations AI.

## 🚀 The Process

### Phase 1: Brainstorming & Design
**Gate**: No code until the design is approved.
1. **Explore Context**: Review the existing codebase and relevant documentation.
2. **Clarify Requirements**: Ask questions one-by-one to understand the "What" and "Why".
3. **Propose Approaches**: List 2-3 technical approaches with trade-offs.
4. **Finalize Design**: Present the chosen architecture and get approval.

### Phase 2: Writing the Plan
1. **Bite-Sized Tasks**: Break the implementation into 2-5 minute actionable steps.
2. **Define Success**: Every task must have a verification step (test case or manual check).
3. **Pathing**: Specify exact file paths and line ranges for every modification.

### Phase 3: Execution Readiness
1. **Commit Early**: Plan for frequent commits following each small task.
2. **Test First**: Ensure every component has a test-first approach.

## 🚩 Red Flags
- Starting to code before the design is approved.
- Large, vague tasks (eg: "Implement Auth").
- Skipping the "Trade-offs" section during approach selection.

> [!TIP]
> Use the [brainstorming](file:///Users/mac/claude-code-proxy/.agents/skills/brainstorming/SKILL.md) and [writing-plans](file:///Users/mac/claude-code-proxy/.agents/skills/writing-plans/SKILL.md) skills for detailed process instructions.

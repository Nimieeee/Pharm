---
name: cot-reasoning
description: Use high-quality Chain-of-Thought (CoT) examples to solve complex coding, architecture, or logic problems.
---

# CoT Reasoning Skill

Use this skill when you encounter a problem that requires deep logical deduction, complex architectural planning, or multi-step algorithmic design.

## How to use

1.  **Identify the Core Problem**: Before writing code, summarize the complex part of the task.
2.  **Retrieve Relevant Thinking**: Call the local CoT retriever to find how similar problems were reasoned through.
    ```bash
    python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Your problem description here"
    ```
3.  **Incorporate Patterns**: Look at the "Internal thinking" (Process) of the retrieved examples. 
    - **Step 3.1: Pre-emptive Error Analysis**: Per high-quality CoT, explicitly identify **"What could go wrong?"** (e.g., exceptions, edge cases, state corruption) BEFORE finalizing the implementation plan.
    - Does it use a specific data structure?
    - How does it handle edge cases?
    - What is the step-by-step breakdown?
4.  **Embody the Thinking**: Use those patterns to construct your own `### Internal Thinking` block before providing the solution.

## When to use
- Implementing new algorithms.
- Refactoring core system services (like the Branching Bug fix).
- Designing new RAG or AI pipelines.
- Solving "puzzle-like" coding requests.

## Expected Outcome
By following retrieved CoT patterns, your solutions should be more robust, consider more edge cases, and follow a clearer logical path, similar to high-end models like OpenAI o1 or Claude 3.5 Sonnet's native reasoning.

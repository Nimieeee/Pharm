---
name: example_skill
description: This is a template skill to show how to structure custom instructions for the AI.
---

# Example Skill Instructions

This is where you write the detailed instructions for the AI to follow when carrying out this specific skill. 

### Guidelines for Writing Good Skills:
1. **Be Specific**: Clearly define what the AI should and should not do.
2. **Step-by-Step**: Break complex workflows into numbered steps.
3. **Context**: Explain *why* certain steps are necessary if it helps the AI make better decisions.
4. **Commands**: If there are specific CLI commands to run, list them exactly.
5. **Code Standards**: If this skill is about writing code, provide examples of the expected style or architecture.

### When to use this skill
The AI will automatically read this file if you ask it to do something related to the `name` or `description` in the YAML block at the top of this file.

### Adding more folders
You can create subfolders right next to this `SKILL.md` file if you want to provide additional context:
- `/scripts`: Place helpful bash or python scripts here.
- `/examples`: Place code examples or reference files here.
- `/resources`: Place templates or static assets here.

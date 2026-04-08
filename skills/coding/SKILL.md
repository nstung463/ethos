---
name: coding
description: Structured approach to implementing, debugging, or refactoring code. Use for any non-trivial coding task to ensure quality and correctness.
---

# Coding Skill

## When to Use

- Implementing a new feature
- Debugging a bug
- Refactoring existing code
- Writing tests

## Workflow

1. **Understand before touching** — read all relevant files first:
   - The file(s) you'll modify
   - Related files (imports, tests, configs)
   - Existing patterns and conventions

2. **Plan with todos** for multi-file changes:
   ```
   write_todos(["Read X", "Implement Y in file A", "Update tests in file B", "Verify"])
   ```

3. **Implement incrementally**:
   - Make the smallest correct change
   - Follow existing naming, formatting, and structure
   - Don't add features beyond what was asked (YAGNI)

4. **Verify**:
   - Re-read the changed file to catch errors
   - Check that imports are correct
   - Trace through the logic for edge cases

5. **Report** what was changed and any important decisions made.

## Principles

- **KISS**: Simplest correct solution wins.
- **DRY**: Don't duplicate logic that already exists.
- **YAGNI**: Don't add abstractions for hypothetical future needs.
- Read before you write. Always.

## For Large Tasks

Delegate to the `coder` subagent to isolate context:
```
task(
  description="Implement [specific feature] in [file]. Requirements: [details]. Follow existing patterns. Return: what was implemented.",
  subagent_type="coder"
)
```

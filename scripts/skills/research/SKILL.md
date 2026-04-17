---
name: research
description: Structured approach to conducting thorough web research on a topic. Use when the user asks you to research something or when you need current information not in the codebase.
---

# Research Skill

## When to Use

- User asks you to research a topic
- You need current information (news, docs, library versions, etc.)
- You need to compare multiple options or approaches

## Workflow

1. **Clarify the scope** — if the research goal is vague, ask one targeted question before searching.

2. **Plan your searches** — use `think` to decide what queries will cover the topic thoroughly. Plan at least 3 distinct angles.

3. **Delegate to researcher subagent** (preferred for deep research):
   ```
   task(
     description="Research [topic]. Find: [specific questions]. Return: key findings, sources, and any caveats.",
     subagent_type="researcher"
   )
   ```
   Or search directly with `tavily_search` for quick lookups.

4. **Synthesize** — don't just dump results. Organize findings into:
   - Key facts / conclusions
   - Relevant sources (URLs)
   - Gaps or uncertainties

5. **Present clearly** — use headers and bullet points for readability.

## Tips

- Use multiple searches with different query angles for comprehensive coverage.
- Note the date of sources — web content may be outdated.
- Always distinguish between facts and speculation.

---
name: analysis
description: Structured approach to analyzing code, data, logs, or documents. Returns prioritized findings and actionable recommendations.
---

# Analysis Skill

## When to Use

- Code review or audit
- Performance analysis
- Security review
- Data analysis
- Log investigation
- Document summarization

## Workflow

1. **Define the analysis goal** — what question are you answering?
   - "What are the security vulnerabilities?"
   - "Why is this slow?"
   - "What does this codebase do?"

2. **Gather the material** — read all relevant files before analyzing.
   Use `glob` and `grep` to scope the analysis efficiently.

3. **Reason carefully** — use `think` before drawing conclusions:
   - What patterns do you see?
   - What's unexpected or concerning?
   - What evidence supports each finding?

4. **Delegate for deep analysis**:
   ```
   task(
     description="Analyze [X] for [goal]. Read files: [list]. Return: prioritized findings with evidence, and recommendations.",
     subagent_type="analyst"
   )
   ```

5. **Structure your output**:
   - **Summary**: One paragraph of what was analyzed and the overall conclusion
   - **Findings**: Numbered, prioritized list (most important first)
   - **Recommendations**: Specific, actionable next steps

## Tips

- Evidence > assertion. Back every finding with a specific line/file.
- Prioritize findings by severity or impact.
- Distinguish between confirmed issues and suspicions.

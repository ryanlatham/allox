# Plan Gate Prompt

Read `AGENTS.md`, then review the plan packet at:

`[[PACKET_PATH]]`

Return JSON only with this shape:

```json
{
  "summary": "short summary",
  "findings": [
    {
      "title": "issue title",
      "body": "actionable explanation",
      "severity": "low|medium|high",
      "category": "optional category",
      "path": "optional file path",
      "line": 1
    }
  ]
}
```

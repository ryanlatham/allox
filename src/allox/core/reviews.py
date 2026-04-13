from __future__ import annotations

import json
import re
from dataclasses import dataclass


class ReviewParseError(ValueError):
    """Raised when reviewer output cannot be parsed safely."""


FENCED_JSON_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


@dataclass
class NormalizedReview:
    reviewer: str
    gate: str
    summary: str
    findings: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {
            "reviewer": self.reviewer,
            "gate": self.gate,
            "summary": self.summary,
            "findings": self.findings,
        }


def _extract_json(raw: str) -> str:
    stripped = raw.strip()
    fenced = FENCED_JSON_RE.search(stripped)
    if fenced:
        return fenced.group(1)
    return stripped


def normalize_review_output(raw: str, reviewer: str, gate: str) -> NormalizedReview:
    try:
        data = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        raise ReviewParseError(f"reviewer output is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReviewParseError("reviewer output must be a JSON object")
    summary = data.get("summary")
    findings = data.get("findings")
    if not isinstance(summary, str):
        raise ReviewParseError("review summary must be a string")
    if not isinstance(findings, list):
        raise ReviewParseError("review findings must be a list")
    normalized_findings: list[dict[str, object]] = []
    for index, item in enumerate(findings):
        if not isinstance(item, dict):
            raise ReviewParseError(f"finding {index} is not an object")
        title = item.get("title")
        body = item.get("body")
        severity = item.get("severity", "medium")
        if not isinstance(title, str) or not isinstance(body, str):
            raise ReviewParseError(f"finding {index} must contain string title/body")
        normalized_findings.append(
            {
                "title": title,
                "body": body,
                "severity": severity if isinstance(severity, str) else "medium",
                "category": item.get("category") if isinstance(item.get("category"), str) else None,
                "path": item.get("path") if isinstance(item.get("path"), str) else None,
                "line": item.get("line") if isinstance(item.get("line"), int) else None,
            }
        )
    return NormalizedReview(reviewer=reviewer, gate=gate, summary=summary, findings=normalized_findings)

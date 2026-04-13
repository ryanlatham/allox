from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

DEFAULT_EXCLUDED_GLOBS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    ".git/**",
    "node_modules/**",
    ".venv/**",
    "build/**",
    "dist/**",
    ".allox/state/archive/**",
    ".allox/state/tmp/**",
]

SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s\"']+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(token\s*[:=]\s*)([^\s\"']+)"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)([^\s\"']+)"), r"\1[REDACTED]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
]


def load_redaction_config(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"excluded_globs": list(DEFAULT_EXCLUDED_GLOBS), "max_file_bytes": 200000}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "excluded_globs": list(data.get("excluded_globs") or DEFAULT_EXCLUDED_GLOBS),
        "max_file_bytes": int(data.get("max_file_bytes") or 200000),
    }


def is_excluded(relative_path: str, config: dict[str, object]) -> bool:
    normalized = relative_path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in config["excluded_globs"])


def redact_text(text: str) -> str:
    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def is_binary_file(path: Path) -> bool:
    data = path.read_bytes()
    return b"\x00" in data

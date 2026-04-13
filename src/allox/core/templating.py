from __future__ import annotations

import re

PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


class TemplateRenderError(KeyError):
    """Raised when a required template variable is missing."""


def render_text(text: str, context: dict[str, object]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise TemplateRenderError(f"missing template variable: {key}")
        return str(context[key])

    return PLACEHOLDER_RE.sub(replace, text)


def render_runtime_text(text: str, context: dict[str, object]) -> str:
    rendered = text
    for key, value in context.items():
        rendered = rendered.replace(f"[[{key}]]", str(value))
    return rendered

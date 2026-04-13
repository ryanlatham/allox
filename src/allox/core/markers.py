from __future__ import annotations

from dataclasses import dataclass


class MarkerError(ValueError):
    """Raised when a section-managed file cannot be parsed safely."""


@dataclass(frozen=True)
class MarkerRange:
    start: int
    inner_start: int
    inner_end: int
    end: int


def find_marker_range(text: str, marker_start: str, marker_end: str) -> MarkerRange:
    start_count = text.count(marker_start)
    end_count = text.count(marker_end)
    if start_count != 1 or end_count != 1:
        raise MarkerError(
            f"expected exactly one managed section, found {start_count} starts and {end_count} ends"
        )
    start_index = text.find(marker_start)
    end_index = text.find(marker_end, start_index + len(marker_start))
    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise MarkerError("managed markers are missing or out of order")
    return MarkerRange(
        start=start_index,
        inner_start=start_index + len(marker_start),
        inner_end=end_index,
        end=end_index + len(marker_end),
    )


def extract_managed_block(text: str, marker_start: str, marker_end: str) -> str:
    marker_range = find_marker_range(text, marker_start, marker_end)
    return text[marker_range.start : marker_range.end]


def extract_managed_body(text: str, marker_start: str, marker_end: str) -> str:
    marker_range = find_marker_range(text, marker_start, marker_end)
    return text[marker_range.inner_start : marker_range.inner_end]


def replace_managed_block(
    current_text: str,
    replacement_block: str,
    marker_start: str,
    marker_end: str,
) -> str:
    marker_range = find_marker_range(current_text, marker_start, marker_end)
    return (
        current_text[: marker_range.start]
        + replacement_block
        + current_text[marker_range.end :]
    )

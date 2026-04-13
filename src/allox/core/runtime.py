from __future__ import annotations

import json
import shlex
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .layout import project_layout
from .pathing import ensure_directory
from .redaction import is_binary_file, is_excluded, load_redaction_config, redact_text
from .reviews import normalize_review_output
from .subprocesses import resolve_binary, run_command
from .templating import render_runtime_text


PACKET_DIFF_CHAR_LIMIT = 12000


@dataclass
class RuntimeResult:
    message: str
    paths: list[str]


@dataclass
class GateExecution:
    gate_name: str
    task_id: str
    packet_path: Path
    prompt_path: Path
    paths: list[str]
    checks_path: Path | None = None
    skipped_review_path: Path | None = None


def bootstrap_task(project_root: Path, title: str | None = None) -> RuntimeResult:
    layout = project_layout(project_root)
    task_title = title or "New task"
    task_id = _make_task_id(task_title)
    mapping = {"TASK_ID": task_id, "TASK_TITLE": task_title, "DATE": task_id.split("-")[0]}

    task_path = layout.task_file(task_id)
    plan_path = layout.plan_file(task_id)
    progress_path = layout.progress_file(task_id)

    for template_name, destination in (
        ("TASK.md", task_path),
        ("PLAN.md", plan_path),
        ("PROGRESS.md", progress_path),
    ):
        template_path = layout.runtime_template_file(template_name)
        content = render_runtime_text(template_path.read_text(encoding="utf-8"), mapping)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    return RuntimeResult(
        message=f"Bootstrapped task {task_id}",
        paths=[str(task_path), str(plan_path), str(progress_path)],
    )


def plan_gate(project_root: Path, task_id: str | None = None) -> RuntimeResult:
    resolved_task_id = task_id or _latest_task_id(project_root)
    execution = _execute_gate(project_root, resolved_task_id, "plan_gate")
    return RuntimeResult(message=f"Plan gate complete for {resolved_task_id}", paths=execution.paths)


def milestone_gate(project_root: Path, task_id: str | None = None) -> RuntimeResult:
    resolved_task_id = task_id or _latest_task_id(project_root)
    execution = _execute_gate(project_root, resolved_task_id, "milestone_gate", run_checks=True)
    return RuntimeResult(message=f"Milestone gate complete for {resolved_task_id}", paths=execution.paths)


def closeout(project_root: Path, task_id: str | None = None) -> RuntimeResult:
    layout = project_layout(project_root)
    resolved_task_id = task_id or _latest_task_id(project_root)
    execution = _execute_gate(
        project_root,
        resolved_task_id,
        "final_gate",
        run_checks=True,
        reviewers_optional=True,
        include_prior_reviews=True,
    )
    review_summary, findings_count = _build_review_summary(project_root, resolved_task_id)
    review_inputs = _build_review_inputs(project_root, resolved_task_id)

    archive_dir = ensure_directory(layout.archive_root)
    adjudication_path = archive_dir / f"{resolved_task_id}-adjudication.md"
    closeout_path = archive_dir / f"{resolved_task_id}.md"

    accepted_findings = "- none\n" if findings_count == 0 else "- Record accepted findings here.\n"
    rejected_findings = "- none\n" if findings_count == 0 else "- Record rejected findings and rationale here.\n"
    verification_lines = []
    if execution.checks_path:
        verification_lines.append(f"- final checks: {execution.checks_path.relative_to(project_root).as_posix()}")
    if execution.skipped_review_path:
        verification_lines.append(
            f"- final review skipped by configuration: {execution.skipped_review_path.relative_to(project_root).as_posix()}"
        )
    else:
        final_review_paths = sorted(layout.reviews_root.glob(f"{resolved_task_id}-final_gate-*.json"))
        for review_path in final_review_paths:
            verification_lines.append(f"- final review: {review_path.relative_to(project_root).as_posix()}")

    _write_runtime_artifact(
        project_root,
        "ADJUDICATION.md",
        adjudication_path,
        {
            "TASK_ID": resolved_task_id,
            "REVIEW_INPUTS": review_inputs,
            "REVIEW_SUMMARY": review_summary,
            "ACCEPTED_FINDINGS": accepted_findings.rstrip(),
            "REJECTED_FINDINGS": rejected_findings.rstrip(),
        },
    )
    _write_runtime_artifact(
        project_root,
        "CLOSEOUT.md",
        closeout_path,
        {
            "TASK_ID": resolved_task_id,
            "DATE": resolved_task_id.split("-")[0],
            "REVIEW_STATUS": review_summary,
            "VERIFICATION": "\n".join(verification_lines) if verification_lines else "- no verification artifacts recorded",
        },
    )

    cleaned = _cleanup_tmp(project_root)
    durable_paths = [
        path
        for path in execution.paths
        if not Path(path).resolve().is_relative_to(layout.tmp_root.resolve())
    ]
    return RuntimeResult(
        message=f"Closed out {resolved_task_id}",
        paths=[*durable_paths, str(adjudication_path), str(closeout_path), *cleaned],
    )


def cleanup(project_root: Path) -> RuntimeResult:
    return RuntimeResult(message="Cleaned temporary artifacts", paths=_cleanup_tmp(project_root))


def worktree_setup(project_root: Path) -> RuntimeResult:
    layout = project_layout(project_root)
    tmp_path = ensure_directory(layout.tmp_root)
    info_path = layout.worktree_setup_file
    info = {
        "project_root": str(project_root),
        "tmp_dir": str(tmp_path),
        "note": "This project uses allox project commands for task orchestration.",
    }
    info_path.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return RuntimeResult(message="Prepared worktree helper metadata", paths=[str(info_path)])


def _execute_gate(
    project_root: Path,
    task_id: str,
    gate_name: str,
    run_checks: bool = False,
    reviewers_optional: bool = False,
    include_prior_reviews: bool = False,
) -> GateExecution:
    checks_path = _run_checks(project_root, task_id, gate_name) if run_checks else None
    packet_path = _build_packet(
        project_root,
        task_id,
        gate_name,
        checks_path=checks_path,
        include_prior_reviews=include_prior_reviews,
    )
    prompt_path = _write_prompt(project_root, task_id, gate_name, packet_path)
    review_paths, skipped_review_path = _run_reviewers(
        project_root,
        gate_name,
        task_id,
        prompt_path,
        packet_path,
        optional=reviewers_optional,
    )
    paths: list[str] = []
    if checks_path:
        paths.append(str(checks_path))
    paths.extend([str(packet_path), str(prompt_path), *review_paths])
    if skipped_review_path:
        paths.append(str(skipped_review_path))
    return GateExecution(
        gate_name=gate_name,
        task_id=task_id,
        packet_path=packet_path,
        prompt_path=prompt_path,
        paths=paths,
        checks_path=checks_path,
        skipped_review_path=skipped_review_path,
    )


def _make_task_id(title: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in title).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug or "task"

    return f"{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{slug}"


def _latest_task_id(project_root: Path) -> str:
    layout = project_layout(project_root)
    task_files = sorted(layout.tasks_root.glob("*.md"))
    if not task_files:
        raise RuntimeError("no task artifacts found; run bootstrap-task first")
    return task_files[-1].stem


def _build_packet(
    project_root: Path,
    task_id: str,
    gate_name: str,
    checks_path: Path | None = None,
    include_prior_reviews: bool = False,
) -> Path:
    layout = project_layout(project_root)
    task_path = layout.task_file(task_id)
    plan_path = layout.plan_file(task_id)
    progress_path = layout.progress_file(task_id)
    packet_path = layout.packet_file(task_id, gate_name)
    packet_path.parent.mkdir(parents=True, exist_ok=True)

    parts = [
        f"# {gate_name.replace('_', ' ').title()} Packet",
        "",
        "## Task",
        redact_text(task_path.read_text(encoding="utf-8")),
        "",
        "## Plan",
        redact_text(plan_path.read_text(encoding="utf-8")),
    ]

    if progress_path.exists():
        parts.extend(["", "## Progress", redact_text(progress_path.read_text(encoding="utf-8"))])

    if checks_path and checks_path.exists():
        parts.extend(["", "## Deterministic Checks", redact_text(checks_path.read_text(encoding="utf-8"))])

    diff_block = _collect_git_snapshot(project_root)
    if diff_block:
        parts.extend(["", "## Git Snapshot", diff_block])

    if include_prior_reviews:
        prior_reviews = _collect_prior_review_summaries(project_root, task_id)
        parts.extend(["", "## Prior Reviews", *prior_reviews])

    parts.extend(["", "## Changed Files"])
    parts.extend(_collect_changed_files(project_root))
    packet_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    return packet_path


def _collect_git_snapshot(project_root: Path) -> str:
    git = resolve_binary("git")
    if not git:
        return "git not available"

    status = run_command([git, "status", "--short"], cwd=project_root)
    diff_stat = run_command([git, "diff", "--stat"], cwd=project_root)
    unified_diff = run_command([git, "diff", "--unified=3", "--no-ext-diff", "--no-color"], cwd=project_root)
    lines = []
    if status.stdout.strip():
        lines.append("### git status --short")
        lines.append(status.stdout.strip())
    if diff_stat.stdout.strip():
        lines.append("### git diff --stat")
        lines.append(diff_stat.stdout.strip())
    if unified_diff.stdout.strip():
        lines.append("### git diff --unified=3")
        lines.append(_truncate_text(unified_diff.stdout.strip(), PACKET_DIFF_CHAR_LIMIT))
    if not lines:
        return "Working tree clean."
    return "\n\n".join(lines)


def _collect_changed_files(project_root: Path) -> list[str]:
    layout = project_layout(project_root)
    config = load_redaction_config(layout.review_redactions_file)
    git = resolve_binary("git")
    changed_paths: list[str] = []
    if git:
        status = run_command([git, "status", "--short"], cwd=project_root)
        for line in status.stdout.splitlines():
            if not line.strip():
                continue
            path = line[3:].strip()
            if path:
                changed_paths.append(path)

    output: list[str] = []
    for relative in changed_paths[:20]:
        if is_excluded(relative, config):
            continue
        file_path = project_root / relative
        if not file_path.exists() or file_path.is_dir():
            continue
        if is_binary_file(file_path):
            continue
        text = file_path.read_text(encoding="utf-8", errors="replace")
        output.extend([f"### {relative}", "```text", redact_text(text[:4000]), "```", ""])
    return output or ["No eligible changed files were captured."]


def _collect_prior_review_summaries(project_root: Path, task_id: str) -> list[str]:
    review_dir = project_layout(project_root).reviews_root
    summaries: list[str] = []
    for review_path in sorted(review_dir.glob(f"{task_id}-*.json")):
        try:
            payload = json.loads(review_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        gate = payload.get("gate") or review_path.stem
        reviewer = payload.get("reviewer") or "reviewer"
        summary = payload.get("summary") or "no summary"
        findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
        summaries.extend(
            [
                f"### {gate} / {reviewer}",
                f"- summary: {summary}",
                f"- findings: {len(findings)}",
                "",
            ]
        )
    return summaries or ["No prior normalized review outputs were found."]


def _write_prompt(project_root: Path, task_id: str, gate_name: str, packet_path: Path) -> Path:
    layout = project_layout(project_root)
    template_path = layout.prompt_template_file(gate_name)
    prompt_path = layout.tmp_root / f"{task_id}-{gate_name}-prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    content = render_runtime_text(
        template_path.read_text(encoding="utf-8"),
        {"TASK_ID": task_id, "PACKET_PATH": str(packet_path), "PROJECT_ROOT": str(project_root)},
    )
    prompt_path.write_text(content, encoding="utf-8")
    return prompt_path


def _load_project_commands(project_root: Path) -> dict[str, object]:
    config_path = project_layout(project_root).project_commands_file
    return json.loads(config_path.read_text(encoding="utf-8"))


def _checks_for_gate(config: dict[str, object], gate_name: str) -> list[object]:
    checks = config.get("checks")
    if isinstance(checks, dict):
        gate_checks = checks.get(gate_name)
        return list(gate_checks) if isinstance(gate_checks, list) else []
    if isinstance(checks, list) and gate_name in {"milestone_gate", "final_gate"}:
        return list(checks)
    return []


def _run_checks(project_root: Path, task_id: str, gate_name: str) -> Path:
    layout = project_layout(project_root)
    config = _load_project_commands(project_root)
    checks = _checks_for_gate(config, gate_name)
    output_path = layout.review_checks_file(task_id, gate_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not checks:
        output_path.write_text("No deterministic checks configured for this gate.\n", encoding="utf-8")
        return output_path

    chunks: list[str] = []
    for entry in checks:
        if isinstance(entry, str):
            command = entry
        elif isinstance(entry, dict) and entry.get("command"):
            command = entry["command"]
        else:
            continue
        result = run_command(command, cwd=project_root)
        chunks.extend(
            [
                f"$ {_display_command(command)}",
                result.stdout.rstrip(),
                result.stderr.rstrip(),
                f"[exit {result.returncode}]",
                "",
            ]
        )
        if result.returncode != 0:
            output_path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")
            raise RuntimeError(f"deterministic check failed: {_display_command(command)}")
    output_path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")
    return output_path


def _run_reviewers(
    project_root: Path,
    gate_name: str,
    task_id: str,
    prompt_path: Path,
    packet_path: Path,
    optional: bool = False,
) -> tuple[list[str], Path | None]:
    config = _load_project_commands(project_root)
    reviewer_config = config.get("reviewers")
    gate_entries = None
    if isinstance(reviewer_config, dict):
        gate_entries = reviewer_config.get(gate_name)
    if gate_entries is None:
        if optional:
            return [], _write_skip_note(project_root, task_id, gate_name)
        raise RuntimeError(
            f"no reviewers are configured for {gate_name}; update allox/config/project_commands.json before running reviewer gates"
        )

    reviewers = [
        reviewer
        for reviewer in list(gate_entries or [])
        if isinstance(reviewer, dict) and _reviewer_is_enabled(reviewer)
    ]
    if not reviewers:
        if optional:
            return [], _write_skip_note(project_root, task_id, gate_name)
        raise RuntimeError(
            f"no reviewers are enabled for {gate_name}; update allox/config/project_commands.json before running reviewer gates"
        )

    prompt_text = prompt_path.read_text(encoding="utf-8")
    layout = project_layout(project_root)
    written: list[str] = []
    for reviewer in reviewers:
        name = str(reviewer.get("name") or "reviewer")
        command = reviewer.get("command")
        if not command:
            raise RuntimeError(f"reviewer {name} is missing a command definition")
        prepared = _prepare_command(command, project_root, packet_path, prompt_path, prompt_text)
        raw_result = run_command(
            prepared,
            cwd=project_root,
            input_text=prompt_text if reviewer.get("stdin") else None,
        )
        if raw_result.returncode != 0:
            raise RuntimeError(
                f"reviewer {name} failed with exit code {raw_result.returncode}: {raw_result.stderr.strip()}"
            )
        raw_path = layout.review_raw_file(task_id, gate_name, name)
        raw_path.write_text(raw_result.stdout, encoding="utf-8")
        normalized = normalize_review_output(raw_result.stdout, reviewer=name, gate=gate_name)
        normalized_path = layout.review_normalized_file(task_id, gate_name, name)
        normalized_path.write_text(
            json.dumps(normalized.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.extend([str(raw_path), str(normalized_path)])
    return written, None


def _reviewer_is_enabled(reviewer: dict[str, object]) -> bool:
    enabled = reviewer.get("enabled")
    if isinstance(enabled, bool):
        return enabled
    if isinstance(enabled, str):
        normalized = enabled.strip().lower()
        if normalized in {"false", "off", "no"}:
            return False
        if normalized in {"true", "on", "yes"}:
            return True
        if normalized == "auto":
            provider = reviewer.get("provider")
            if isinstance(provider, str) and provider.strip():
                return resolve_binary(provider) is not None
    return bool(enabled)


def _prepare_command(
    command: object,
    project_root: Path,
    packet_path: Path,
    prompt_path: Path,
    prompt_text: str,
) -> list[str] | str:
    replacements = {
        "project_root": str(project_root),
        "packet_path": str(packet_path),
        "prompt_path": str(prompt_path),
        "prompt": prompt_text,
    }
    if isinstance(command, str):
        return command.format(**replacements)
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        raise RuntimeError("reviewer command must be a string or argv list")
    prepared = [item.format(**replacements) for item in command]
    if prepared:
        binary = resolve_binary(prepared[0]) or prepared[0]
        prepared[0] = binary
    return prepared


def _write_skip_note(project_root: Path, task_id: str, gate_name: str) -> Path:
    skip_path = project_layout(project_root).review_skip_file(task_id, gate_name)
    skip_path.parent.mkdir(parents=True, exist_ok=True)
    skip_path.write_text(
        f"No {gate_name} reviewers are enabled; reviewer execution was skipped by configuration.\n",
        encoding="utf-8",
    )
    return skip_path


def _build_review_summary(project_root: Path, task_id: str) -> tuple[str, int]:
    layout = project_layout(project_root)
    lines: list[str] = []
    total_findings = 0
    for review_path in sorted(layout.reviews_root.glob(f"{task_id}-*.json")):
        try:
            payload = json.loads(review_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        reviewer = payload.get("reviewer") or review_path.stem
        gate = payload.get("gate") or "unknown"
        summary = payload.get("summary") or "no summary"
        findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
        total_findings += len(findings)
        lines.append(f"- {gate} / {reviewer}: {summary} ({len(findings)} findings)")
    skipped = sorted(layout.reviews_root.glob(f"{task_id}-*-skipped.txt"))
    for skip_path in skipped:
        lines.append(f"- {skip_path.stem}: skipped by configuration")
    return ("\n".join(lines) if lines else "- no review outputs recorded"), total_findings


def _build_review_inputs(project_root: Path, task_id: str) -> str:
    review_dir = project_layout(project_root).reviews_root
    inputs = [
        path.relative_to(project_root).as_posix()
        for path in sorted(review_dir.glob(f"{task_id}-*"))
        if path.is_file()
    ]
    if not inputs:
        return "- no review inputs recorded"
    return "\n".join(f"- {item}" for item in inputs)


def _write_runtime_artifact(
    project_root: Path,
    template_name: str,
    destination: Path,
    mapping: dict[str, object],
) -> None:
    template_path = project_layout(project_root).runtime_template_file(template_name)
    content = render_runtime_text(template_path.read_text(encoding="utf-8"), mapping)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def _cleanup_tmp(project_root: Path) -> list[str]:
    layout = project_layout(project_root)
    cleaned: list[str] = []
    tmp_path = layout.tmp_root
    if tmp_path.exists():
        for child in tmp_path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
            cleaned.append(str(child))
    return cleaned


def _display_command(command: list[str] | str) -> str:
    if isinstance(command, str):
        return command
    return shlex.join(command)


def _truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"

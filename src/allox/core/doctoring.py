from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

from ..version import __version__
from .manifest import ProjectManifest, manifest_path
from .pathing import find_project_root
from .subprocesses import probe_binary, run_command


ONLINE_TIMEOUT_SECONDS = 8.0


def collect_doctor_report(project_path: Path | None = None, online: bool = False) -> dict[str, object]:
    resolved_project = project_path.resolve() if project_path else find_project_root(Path.cwd())

    binaries = {
        "git": probe_binary("git"),
        "codex": probe_binary("codex"),
        "claude": probe_binary("claude"),
        "gemini": probe_binary("gemini"),
    }
    if online:
        for name in ("codex", "claude", "gemini"):
            binaries[name].update(_probe_online_status(name, binaries[name]))

    report: dict[str, object] = {
        "framework_version": __version__,
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "supported": sys.version_info >= (3, 9),
        },
        "binaries": binaries,
    }

    if resolved_project:
        project_info: dict[str, object] = {"path": str(resolved_project)}
        manifest_file = manifest_path(resolved_project)
        if manifest_file.exists():
            manifest = ProjectManifest.read(manifest_file)
            project_info.update(
                {
                    "managed": True,
                    "project_name": manifest.project_name,
                    "template": manifest.template,
                    "template_version": manifest.template_version,
                    "framework_version": manifest.framework_version,
                    "version_match": manifest.framework_version == __version__,
                }
            )
        else:
            project_info.update({"managed": False, "error": "manifest not found"})
        report["project"] = project_info

    return report


def _probe_online_status(name: str, binary_report: dict[str, object]) -> dict[str, object]:
    if not binary_report.get("found"):
        return {
            "online_ready": False,
            "auth_status": "unavailable",
            "online_note": "binary is not available for online readiness checks",
        }

    path = str(binary_report.get("path") or name)
    if name == "codex":
        return _probe_codex_online(path)
    if name == "claude":
        return _probe_claude_online(path)
    if name == "gemini":
        return _probe_gemini_online(path)
    return {"online_ready": False, "auth_status": "not_checked"}


def _probe_codex_online(path: str) -> dict[str, object]:
    result = run_command([path, "login", "status"], timeout_seconds=ONLINE_TIMEOUT_SECONDS)
    detail = (result.stdout or result.stderr).strip()
    if result.returncode == 0 and "logged in" in detail.lower():
        return {
            "online_ready": True,
            "auth_status": "authenticated",
            "online_note": detail or "codex login status succeeded",
        }
    return {
        "online_ready": False,
        "auth_status": "not_authenticated",
        "online_note": detail or "codex login status did not confirm an authenticated session",
    }


def _probe_claude_online(path: str) -> dict[str, object]:
    result = run_command([path, "auth", "status", "--json"], timeout_seconds=ONLINE_TIMEOUT_SECONDS)
    if result.returncode != 0:
        return {
            "online_ready": False,
            "auth_status": "not_authenticated",
            "online_note": (result.stderr or result.stdout).strip() or "claude auth status failed",
        }
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "online_ready": False,
            "auth_status": "unknown",
            "online_note": "claude auth status returned malformed JSON",
        }
    if payload.get("loggedIn") is True:
        auth_method = payload.get("authMethod") or "authenticated"
        return {
            "online_ready": True,
            "auth_status": "authenticated",
            "online_note": f"authenticated via {auth_method}",
        }
    return {
        "online_ready": False,
        "auth_status": "not_authenticated",
        "online_note": "claude auth status reported loggedIn=false",
    }


def _probe_gemini_online(path: str) -> dict[str, object]:
    result = run_command(
        [path, "--approval-mode", "plan", "--output-format", "text", "-p", "Reply with OK only."],
        timeout_seconds=ONLINE_TIMEOUT_SECONDS,
    )
    if result.returncode == 0:
        return {
            "online_ready": True,
            "auth_status": "ready",
            "online_note": "best-effort headless Gemini probe succeeded",
        }
    note = (result.stderr or result.stdout).strip() or "best-effort Gemini probe failed"
    if result.timed_out:
        note = "best-effort Gemini probe timed out"
    return {
        "online_ready": False,
        "auth_status": "probe_failed",
        "online_note": note,
    }


def format_doctor_report(report: dict[str, object]) -> str:
    lines = [
        f"allox {report['framework_version']}",
        f"Python: {report['python']['version']} ({'supported' if report['python']['supported'] else 'unsupported'})",
        "",
        "Binaries:",
    ]
    binaries = report["binaries"]
    for name in ("git", "codex", "claude", "gemini"):
        item = binaries[name]
        if item["found"]:
            version = item.get("version") or "version unavailable"
            source = f", source={item['source']}" if item.get("source") else ""
            lines.append(f"- {name}: {item['path']} [{item['status']}{source}] {version}")
            if item.get("online_ready") is not None:
                readiness = "ready" if item.get("online_ready") else "not ready"
                lines.append(f"  online: {readiness}, auth={item.get('auth_status', 'unknown')}")
            if item.get("note"):
                lines.append(f"  note: {item['note']}")
            if item.get("online_note"):
                lines.append(f"  online note: {item['online_note']}")
        else:
            lines.append(f"- {name}: missing")
    project = report.get("project")
    if project:
        lines.extend(["", "Project:"])
        lines.append(f"- path: {project['path']}")
        if project.get("managed"):
            lines.append(f"- managed: yes ({project['project_name']})")
            lines.append(f"- manifest version: {project['framework_version']}")
            lines.append(f"- version match: {'yes' if project['version_match'] else 'no'}")
        else:
            lines.append(f"- managed: no ({project.get('error', 'unknown state')})")
    return "\n".join(lines)


def doctor_report_json(report: dict[str, object]) -> str:
    return json.dumps(report, indent=2, sort_keys=True)

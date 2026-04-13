from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


ENV_BIN_OVERRIDES = {
    "codex": "ALLOX_CODEX_BIN",
    "claude": "ALLOX_CLAUDE_BIN",
    "gemini": "ALLOX_GEMINI_BIN",
}

DISCOVERY_NAMES = {"codex", "claude", "gemini", "node", "npm", "npx"}


@dataclass
class CommandResult:
    command: list[str] | str
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass(frozen=True)
class BinaryResolution:
    name: str
    path: str
    source: str
    path_hint: str | None = None


def _current_path_entries(env: dict[str, str] | None = None) -> list[str]:
    raw_path = (env or os.environ).get("PATH", "")
    return [entry for entry in raw_path.split(os.pathsep) if entry]


def _path_contains(directory: str, env: dict[str, str] | None = None) -> bool:
    resolved = os.path.realpath(directory)
    return any(os.path.realpath(entry) == resolved for entry in _current_path_entries(env))


def _nvm_candidate_paths(name: str) -> list[Path]:
    if name not in DISCOVERY_NAMES:
        return []
    nvm_root = Path.home() / ".nvm" / "versions" / "node"
    if not nvm_root.exists():
        return []
    candidates = [path for path in nvm_root.glob(f"*/bin/{name}") if path.is_file() or path.is_symlink()]
    return sorted(candidates, key=_nvm_sort_key, reverse=True)


def _nvm_sort_key(path: Path) -> tuple[int, ...]:
    version_name = path.parents[1].name
    if version_name.startswith("v"):
        version_name = version_name[1:]
    parts: list[int] = []
    for chunk in version_name.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    return tuple(parts or [0])


def _discover_binary(name: str) -> str | None:
    direct_candidates = [
        Path.home() / ".local" / "bin" / name,
        Path.home() / "bin" / name,
    ]
    for candidate in direct_candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    for candidate in _nvm_candidate_paths(name):
        if os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def resolve_binary_info(name: str) -> BinaryResolution | None:
    override_name = ENV_BIN_OVERRIDES.get(name)
    override = os.environ.get(override_name, "") if override_name else ""
    if override:
        resolved_override = shutil.which(override) or override
        return BinaryResolution(name=name, path=resolved_override, source="env")

    on_path = shutil.which(name)
    if on_path:
        return BinaryResolution(name=name, path=on_path, source="path")

    discovered = _discover_binary(name)
    if discovered:
        path_hint = str(Path(discovered).parent)
        return BinaryResolution(name=name, path=discovered, source="discovered", path_hint=path_hint)

    return None


def resolve_binary(name: str) -> str | None:
    resolved = resolve_binary_info(name)
    return resolved.path if resolved else None


def build_command_env(
    command: list[str] | str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)

    path_entries: list[str] = []

    if isinstance(command, list) and command:
        first = command[0]
        if os.path.isabs(first):
            first_dir = str(Path(first).parent)
            if first_dir not in path_entries:
                path_entries.append(first_dir)
        elif "/" in first:
            first_dir = str(Path(first).expanduser().resolve().parent)
            if first_dir not in path_entries:
                path_entries.append(first_dir)
        else:
            resolution = resolve_binary_info(first)
            if resolution and resolution.path_hint and resolution.path_hint not in path_entries:
                path_entries.append(resolution.path_hint)

    existing = _current_path_entries(merged_env)
    combined: list[str] = []
    seen: set[str] = set()
    for entry in [*path_entries, *existing]:
        real = os.path.realpath(os.path.expanduser(entry))
        if real in seen:
            continue
        seen.add(real)
        combined.append(os.path.expanduser(entry))
    merged_env["PATH"] = os.pathsep.join(combined)
    return merged_env


def run_command(
    command: list[str] | str,
    cwd: Path | None = None,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> CommandResult:
    command_env = build_command_env(command=command, env=env)
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            input=input_text,
            text=True,
            capture_output=True,
            env=command_env,
            shell=isinstance(command, str),
            check=False,
            timeout=timeout_seconds,
        )
        return CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode("utf-8", errors="replace") if exc.stdout else "")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode("utf-8", errors="replace") if exc.stderr else "")
        return CommandResult(
            command=command,
            returncode=124,
            stdout=stdout,
            stderr=stderr or f"command timed out after {timeout_seconds} seconds",
            timed_out=True,
        )


def probe_binary(name: str, version_args: tuple[str, ...] = ("--version",)) -> dict[str, object]:
    resolution = resolve_binary_info(name)
    result: dict[str, object] = {
        "name": name,
        "configured": bool(resolution),
        "found": bool(resolution),
        "path": resolution.path if resolution else None,
    }
    if not resolution:
        result["status"] = "missing"
        return result
    result["source"] = resolution.source
    if resolution.path_hint and not _path_contains(resolution.path_hint):
        result["path_hint"] = resolution.path_hint
    version = ""
    probe = run_command([resolution.path, *version_args])
    if probe.returncode == 0:
        version = (probe.stdout or probe.stderr).strip().splitlines()[0] if (probe.stdout or probe.stderr) else ""
    result["status"] = "ok" if probe.returncode == 0 else "warning"
    result["version"] = version
    if probe.returncode != 0:
        result["error"] = probe.stderr.strip() or probe.stdout.strip()
        if "No such file or directory" in str(result["error"]) and resolution.path_hint:
            result["note"] = (
                "The binary wrapper was found, but its runtime is not on PATH. "
                f"Prepend {resolution.path_hint} to PATH or set {ENV_BIN_OVERRIDES.get(name, 'the appropriate ALLOX_*_BIN override')}."
            )
    elif resolution.path_hint and not _path_contains(resolution.path_hint):
        result["note"] = (
            "Resolved via fallback discovery outside the current PATH. "
            f"allox will prepend {resolution.path_hint} automatically for child commands."
        )
    return result

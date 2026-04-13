from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectLayout:
    project_root: Path

    @property
    def visible_root(self) -> Path:
        return self.project_root / "allox"

    @property
    def hidden_root(self) -> Path:
        return self.project_root / ".allox"

    @property
    def workflow_readme(self) -> Path:
        return self.visible_root / "README.md"

    @property
    def config_root(self) -> Path:
        return self.visible_root / "config"

    @property
    def prompts_root(self) -> Path:
        return self.visible_root / "prompts"

    @property
    def schemas_root(self) -> Path:
        return self.visible_root / "schemas"

    @property
    def templates_root(self) -> Path:
        return self.visible_root / "templates"

    @property
    def scripts_root(self) -> Path:
        return self.hidden_root / "scripts"

    @property
    def state_root(self) -> Path:
        return self.hidden_root / "state"

    @property
    def tasks_root(self) -> Path:
        return self.state_root / "tasks"

    @property
    def plans_root(self) -> Path:
        return self.state_root / "plans"

    @property
    def progress_root(self) -> Path:
        return self.state_root / "progress"

    @property
    def packets_root(self) -> Path:
        return self.state_root / "packets"

    @property
    def reviews_root(self) -> Path:
        return self.state_root / "reviews"

    @property
    def archive_root(self) -> Path:
        return self.state_root / "archive"

    @property
    def tmp_root(self) -> Path:
        return self.state_root / "tmp"

    @property
    def project_commands_file(self) -> Path:
        return self.config_root / "project_commands.json"

    @property
    def review_redactions_file(self) -> Path:
        return self.config_root / "review_redactions.json"

    def prompt_template_file(self, gate_name: str) -> Path:
        return self.prompts_root / f"{gate_name}.md"

    def schema_file(self, name: str) -> Path:
        return self.schemas_root / name

    def runtime_template_file(self, name: str) -> Path:
        return self.templates_root / name

    def task_file(self, task_id: str) -> Path:
        return self.tasks_root / f"{task_id}.md"

    def plan_file(self, task_id: str) -> Path:
        return self.plans_root / f"{task_id}.md"

    def progress_file(self, task_id: str) -> Path:
        return self.progress_root / f"{task_id}.md"

    def packet_file(self, task_id: str, gate_name: str) -> Path:
        return self.packets_root / f"{task_id}-{gate_name}.md"

    def review_checks_file(self, task_id: str, gate_name: str) -> Path:
        return self.reviews_root / f"{task_id}-{gate_name}-checks.txt"

    def review_raw_file(self, task_id: str, gate_name: str, reviewer: str) -> Path:
        return self.reviews_root / f"{task_id}-{gate_name}-{reviewer}.raw.txt"

    def review_normalized_file(self, task_id: str, gate_name: str, reviewer: str) -> Path:
        return self.reviews_root / f"{task_id}-{gate_name}-{reviewer}.json"

    def review_skip_file(self, task_id: str, gate_name: str) -> Path:
        return self.reviews_root / f"{task_id}-{gate_name}-skipped.txt"

    def archived_closeout_file(self, task_id: str) -> Path:
        return self.archive_root / f"{task_id}.md"

    def archived_adjudication_file(self, task_id: str) -> Path:
        return self.archive_root / f"{task_id}-adjudication.md"

    @property
    def worktree_setup_file(self) -> Path:
        return self.tmp_root / "worktree-setup.json"

    def conflict_file(self, relative_path: str) -> Path:
        return self.hidden_root / "conflicts" / f"{relative_path}.allox.new"


def project_layout(project_root: Path) -> ProjectLayout:
    return ProjectLayout(project_root=project_root)

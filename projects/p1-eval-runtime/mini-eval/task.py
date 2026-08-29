"""Load tasks/<id>/task.yaml."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Task:
    id: str
    instruction: str
    timeout_sec: float
    verifier: str
    path: Path
    setup: str = ""

    @classmethod
    def from_yaml(cls, yaml_file_path: Path | str) -> "Task":
        yaml_path = Path(yaml_file_path)
        spec = yaml.safe_load(yaml_path.read_text()) or {}
        return cls(
            id=spec.get("id") or yaml_path.parent.name,
            instruction=spec.get("instruction") or "",
            timeout_sec=float(spec.get("timeout_sec") or 10),
            verifier=spec.get("verifier") or "tests/test_result.py",
            path=yaml_path.parent,
            setup=spec.get("setup") or "",
        )

"""One throwaway workspace per trial. Tests never live here."""

import shutil
import subprocess
import tempfile
from pathlib import Path


class DeadlineExceeded(Exception):
    """Command hit timeout_sec. run.py should record status ERROR, not FAIL."""


class Environment:
    def __init__(self, timeout_sec: float = 10) -> None:
        self.path = Path(tempfile.mkdtemp(prefix="p1ws-"))
        self.timeout_sec = timeout_sec
        self.log: list[dict] = []

    def exec(self, command: str, timeout: float | None = None) -> tuple[int, str]:
        limit = self.timeout_sec if timeout is None else timeout
        self.log.append({"type": "command", "value": command})
        try:
            proc = subprocess.run(
                ["bash", "-lc", command],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=limit,
            )
        except subprocess.TimeoutExpired as exc:
            self.log.append({"type": "command_result", "exit_code": 124})
            raise DeadlineExceeded(command) from exc
        out = (proc.stdout or "") + (proc.stderr or "")
        self.log.append({"type": "command_result", "exit_code": proc.returncode})
        return proc.returncode, out

    def cleanup(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)

    def __enter__(self) -> "Environment":
        return self

    def __exit__(self, *_exc) -> None:
        self.cleanup()

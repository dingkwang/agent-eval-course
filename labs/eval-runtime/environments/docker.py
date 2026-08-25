"""Docker backend: host workspace bind-mounted at /workspace, commands via docker run --rm."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from protocol import EnvironmentCapabilities, ExecResult, TaskBundle

from environments.local import LocalLease, PathEscapeError

IMAGE = "python:3.12-slim-bookworm"
WORKSPACE = "/workspace"

_DOCKER_OK: bool | None = None


def docker_available() -> bool:
    global _DOCKER_OK
    if _DOCKER_OK is not None:
        return _DOCKER_OK
    if not shutil.which("docker"):
        _DOCKER_OK = False
        return False
    try:
        probe = subprocess.run(
            ["docker", "run", "--rm", IMAGE, "python3", "-c", "print('ok')"],
            capture_output=True,
            timeout=120,
            check=False,
        )
        _DOCKER_OK = probe.returncode == 0 and b"ok" in probe.stdout
    except (OSError, subprocess.TimeoutExpired):
        _DOCKER_OK = False
    return _DOCKER_OK


class DockerLease(LocalLease):
    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecResult:
        self._check()
        work = str(self._workspace.resolve())
        cmd = ["docker", "run", "--rm", "-v", f"{work}:{WORKSPACE}"]
        if cwd:
            if not cwd.startswith(WORKSPACE):
                raise PathEscapeError(cwd)
            cmd.extend(["-w", cwd])
        else:
            cmd.extend(["-w", WORKSPACE])
        if env:
            for k, v in env.items():
                cmd.extend(["-e", f"{k}={v}"])
        cmd.append(IMAGE)
        cmd.extend(argv)
        try:
            proc = subprocess.run(
                cmd, capture_output=True, timeout=timeout, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ExecResult(124, exc.stdout or b"", b"timeout")
        return ExecResult(proc.returncode, proc.stdout, proc.stderr)


class DockerEnvironment:
    capabilities = EnvironmentCapabilities(isolation="bind-mount", os="linux")

    async def start(self, task: TaskBundle, owner_id: str) -> DockerLease:
        if not docker_available():
            raise RuntimeError("docker not available")
        root = Path(tempfile.mkdtemp(prefix=f"evalrt-docker-{owner_id}-"))
        lease = DockerLease(root, owner_id)
        for path, data in task.fixtures.items():
            await lease.write(path, data)
        return lease

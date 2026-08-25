"""In-process workspace. One TemporaryDirectory per Trial; not a Harbor backend."""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

from protocol import (
    EnvironmentCapabilities,
    EnvironmentLease,
    ExecResult,
    TaskBundle,
)

WORKSPACE = "/workspace"


class LeaseClosedError(RuntimeError):
    pass


class PathEscapeError(ValueError):
    pass


class LocalLease:
    def __init__(self, root: Path, owner_id: str) -> None:
        self._root = root
        self._workspace = root / "workspace"
        self._workspace.mkdir(parents=True, exist_ok=True)
        self.owner_id = owner_id
        self.stopped = False
        self._tmpdir = root

    def _resolve(self, path: str) -> Path:
        if not path.startswith(WORKSPACE):
            raise PathEscapeError(f"path must be under {WORKSPACE}: {path}")
        rel = path[len(WORKSPACE):].lstrip("/")
        target = (self._workspace / rel).resolve()
        try:
            target.relative_to(self._workspace.resolve())
        except ValueError as exc:
            raise PathEscapeError(path) from exc
        return target

    def _check(self) -> None:
        if self.stopped:
            raise LeaseClosedError("lease stopped")

    async def exec(
        self,
        argv: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ExecResult:
        self._check()
        work = self._resolve(cwd) if cwd else self._workspace
        merged = os.environ.copy()
        if env:
            merged.update(env)
        try:
            proc = subprocess.run(
                argv,
                cwd=work,
                env=merged,
                timeout=timeout,
                capture_output=True,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ExecResult(return_code=124, stdout=exc.stdout or b"", stderr=b"timeout")
        return ExecResult(proc.returncode, proc.stdout, proc.stderr)

    async def read(self, path: str) -> bytes:
        self._check()
        return self._resolve(path).read_bytes()

    async def write(self, path: str, data: bytes) -> None:
        self._check()
        dest = self._resolve(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    async def snapshot(self) -> str:
        self._check()
        items: list[tuple[str, str]] = []
        for p in sorted(self._workspace.rglob("*")):
            if p.is_file():
                rel = p.relative_to(self._workspace).as_posix()
                items.append((rel, hashlib.sha256(p.read_bytes()).hexdigest()))
        blob = repr(items).encode()
        return hashlib.sha256(blob).hexdigest()

    async def stop(self) -> None:
        import shutil
        if self.stopped:
            return
        self.stopped = True
        shutil.rmtree(self._tmpdir, ignore_errors=True)


class LocalEnvironment:
    capabilities = EnvironmentCapabilities(isolation="tempdir", os="linux")

    async def start(self, task: TaskBundle, owner_id: str) -> LocalLease:
        root = Path(tempfile.mkdtemp(prefix=f"evalrt-{owner_id}-"))
        lease = LocalLease(root, owner_id)
        for path, data in task.fixtures.items():
            await lease.write(path, data)
        return lease

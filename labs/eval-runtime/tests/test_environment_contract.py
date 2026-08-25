"""Local environment contract. Docker tests live in test_differential."""

import asyncio

import pytest

from environments.local import LeaseClosedError, LocalEnvironment, PathEscapeError
from task_sum import SUM_TASK


def test_fresh_trial_has_fresh_initial_state() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        a = await env.start(SUM_TASK, "t-a")
        await a.write("/workspace/stale.txt", b"old")
        await a.stop()
        b = await env.start(SUM_TASK, "t-b")
        listing = await b.exec(["ls"])
        assert b"stale.txt" not in listing.stdout
        assert b"input.txt" in listing.stdout
        await b.stop()

    asyncio.run(probe())


def test_exec_preserves_stdout_stderr_and_return_code() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-exec")
        ok = await lease.exec(["sh", "-c", "printf hi"])
        assert ok.return_code == 0
        assert ok.stdout == b"hi"
        bad = await lease.exec(["sh", "-c", "echo err >&2; exit 7"])
        assert bad.return_code == 7
        assert b"err" in bad.stderr
        await lease.stop()

    asyncio.run(probe())


def test_cwd_and_env_have_defined_precedence() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-cwd")
        await lease.write("/workspace/sub/x.txt", b"x")
        got = await lease.exec(["pwd"], cwd="/workspace/sub")
        assert got.stdout.decode().strip().endswith("sub")
        got_env = await lease.exec(["sh", "-c", "printf $FOO"], env={"FOO": "bar"})
        assert got_env.stdout == b"bar"
        await lease.stop()

    asyncio.run(probe())


def test_file_round_trip_preserves_bytes() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-bytes")
        payload = b"\x00\xff binary"
        await lease.write("/workspace/bin.dat", payload)
        assert await lease.read("/workspace/bin.dat") == payload
        await lease.stop()

    asyncio.run(probe())


def test_path_escape_is_rejected() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-esc")
        with pytest.raises(PathEscapeError):
            await lease.read("/etc/passwd")
        with pytest.raises(PathEscapeError):
            await lease.read("/workspace/../etc/passwd")
        await lease.stop()

    asyncio.run(probe())


def test_stop_is_idempotent() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-stop")
        await lease.stop()
        await lease.stop()

    asyncio.run(probe())


def test_operations_after_stop_are_rejected() -> None:
    async def probe() -> None:
        env = LocalEnvironment()
        lease = await env.start(SUM_TASK, "t-after")
        await lease.stop()
        with pytest.raises(LeaseClosedError):
            await lease.read("/workspace/input.txt")

    asyncio.run(probe())

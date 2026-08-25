"""Every injected fault still produces a terminal status and attempts cleanup."""

import asyncio

import pytest

from environments.local import LocalEnvironment
from task_sum import SUM_TASK, oracle
from trial import FAULTS, run_trial


@pytest.mark.parametrize("fault_at", sorted(FAULTS))
def test_every_failure_path_has_terminal_result_and_cleanup(fault_at: str) -> None:
    result = asyncio.run(
        run_trial(
            oracle(),
            LocalEnvironment(),
            SUM_TASK,
            f"t-{fault_at}",
            fault_at=fault_at,
        )
    )
    assert result.status != "SUCCEEDED"
    assert result.cleanup
    assert result.owner_id.startswith("t-")
    assert result.original_error or result.status == "CLEANUP_ERROR"


def test_cancelled_still_stops_the_environment() -> None:
    result = asyncio.run(
        run_trial(oracle(), LocalEnvironment(), SUM_TASK, "t-cancel", fault_at="cancelled")
    )
    assert result.status == "CANCELLED"
    assert result.cleanup
    assert "END" in result.recorder.events
    assert "VERIFY" not in result.recorder.events


def test_happy_path_has_owner_and_end() -> None:
    result = asyncio.run(run_trial(oracle(), LocalEnvironment(), SUM_TASK, "t-ok"))
    assert result.status == "SUCCEEDED"
    assert result.cleanup
    assert "END" in result.recorder.events
    assert result.owner_id == "t-ok"

"""Every injected fault still produces a terminal status and attempts cleanup."""

import asyncio

import pytest

from adapters.oracle import OracleAgent
from environments.local import LocalEnvironment
from task_sum import SUM_TASK
from trial import FAULTS, run_trial


@pytest.mark.parametrize("fault_at", sorted(FAULTS))
def test_every_failure_path_has_terminal_result_and_cleanup(fault_at: str) -> None:
    result = asyncio.run(
        run_trial(
            OracleAgent(),
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


def test_happy_path_has_owner_and_end() -> None:
    result = asyncio.run(run_trial(OracleAgent(), LocalEnvironment(), SUM_TASK, "t-ok"))
    assert result.status == "SUCCEEDED"
    assert result.cleanup
    assert "END" in result.recorder.events
    assert result.owner_id == "t-ok"

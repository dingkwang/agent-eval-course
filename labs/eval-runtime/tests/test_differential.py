"""Null/Oracle/scripted probes across backends."""

import asyncio

import pytest

from adapters.null_agent import NullAgent
from adapters.scripted import ScriptedInvalidAgent, ScriptedValidAgent
from environments.docker import DockerEnvironment, docker_available
from environments.local import LocalEnvironment
from task_sum import SUM_TASK, oracle
from trial import run_trial

needs_docker = pytest.mark.skipif(not docker_available(), reason="docker daemon not available")


def test_null_fails_on_local() -> None:
    result = asyncio.run(run_trial(NullAgent(), LocalEnvironment(), SUM_TASK, "t-null-l"))
    assert result.reward == 0.0
    assert result.status == "FAILED"


def test_oracle_passes_on_local() -> None:
    result = asyncio.run(run_trial(oracle(), LocalEnvironment(), SUM_TASK, "t-ora-l"))
    assert result.reward == 1.0


def test_scripted_invalid_fails_on_local() -> None:
    result = asyncio.run(
        run_trial(ScriptedInvalidAgent(), LocalEnvironment(), SUM_TASK, "t-bad-l")
    )
    assert result.reward == 0.0


def test_scripted_valid_passes_on_local() -> None:
    result = asyncio.run(
        run_trial(ScriptedValidAgent(), LocalEnvironment(), SUM_TASK, "t-ok-l")
    )
    assert result.reward == 1.0
    assert result.status == "SUCCEEDED"


@needs_docker
def test_null_fails_on_docker() -> None:
    result = asyncio.run(run_trial(NullAgent(), DockerEnvironment(), SUM_TASK, "t-null-d"))
    assert result.reward == 0.0


@needs_docker
def test_oracle_passes_on_docker() -> None:
    result = asyncio.run(run_trial(oracle(), DockerEnvironment(), SUM_TASK, "t-ora-d"))
    assert result.reward == 1.0


@needs_docker
def test_scripted_valid_has_same_final_state_digest() -> None:
    local = asyncio.run(
        run_trial(ScriptedValidAgent(), LocalEnvironment(), SUM_TASK, "t-dig-l")
    )
    docker = asyncio.run(
        run_trial(ScriptedValidAgent(), DockerEnvironment(), SUM_TASK, "t-dig-d")
    )
    assert local.status == docker.status == "SUCCEEDED"
    assert local.final_digest == docker.final_digest
    assert local.final_digest is not None


@needs_docker
def test_backends_produce_same_verifier_input_digest() -> None:
    local = asyncio.run(
        run_trial(ScriptedValidAgent(), LocalEnvironment(), SUM_TASK, "t-ver-l")
    )
    docker = asyncio.run(
        run_trial(ScriptedValidAgent(), DockerEnvironment(), SUM_TASK, "t-ver-d")
    )
    assert local.reward == docker.reward == 1.0
    assert local.final_digest == docker.final_digest

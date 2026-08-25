from protocol import TaskBundle

SUM_TASK = TaskBundle(
    task_id="sum-numbers",
    instruction=(
        "Read /workspace/input.txt, add the two integers, "
        "and write only the result to /workspace/answer.txt."
    ),
    fixtures={"/workspace/input.txt": b"19 23\n"},
    hidden={"expected": b"42\n"},
)

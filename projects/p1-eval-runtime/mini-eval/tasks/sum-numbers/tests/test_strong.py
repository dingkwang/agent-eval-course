import random
import subprocess
import sys
from pathlib import Path

out = subprocess.run(
    [sys.executable, "sum.py"],
    capture_output=True,
    text=True,
    timeout=30,
)
assert out.returncode == 0, out.stderr
assert out.stdout.strip() == "42", f"original input: got {out.stdout!r}"

nums = [random.randint(1, 999) for _ in range(5)]
Path("numbers.txt").write_text("\n".join(map(str, nums)) + "\n")
out = subprocess.run(
    [sys.executable, "sum.py"],
    capture_output=True,
    text=True,
    timeout=30,
)
assert out.returncode == 0, out.stderr
assert out.stdout.strip() == str(sum(nums)), "hardcoded answer? verifier changed the input"

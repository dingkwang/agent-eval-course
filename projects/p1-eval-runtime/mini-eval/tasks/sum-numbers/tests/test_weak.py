import subprocess
import sys

out = subprocess.run(
    [sys.executable, "sum.py"],
    capture_output=True,
    text=True,
    timeout=30,
)
assert out.returncode == 0, out.stderr
assert out.stdout.strip() == "42", f"got {out.stdout!r}"

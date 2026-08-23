"""Launch the artifact, poll it, kill it. The verifier owns the process lifecycle.

Note the retry loop: without it this test is a coin flip on a loaded machine.
That single `for` loop is the difference between a benchmark and a flaky one
(W6, Infra Noise).
"""

import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

PORT = 8080


def test_artifact_exists():
    assert Path("/workspace/server.py").exists()


def test_server_responds():
    proc = subprocess.Popen(["python3", "/workspace/server.py"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        body, last = None, None
        for _ in range(40):                       # up to ~4s of startup slack
            try:
                body = urllib.request.urlopen(f"http://127.0.0.1:{PORT}", timeout=1).read()
                break
            except (urllib.error.URLError, ConnectionError, OSError) as e:
                last = e
                time.sleep(0.1)
        assert body is not None, f"server never came up: {last}"
        assert body.strip() == b"hello", f"got {body!r}"
    finally:
        proc.terminate()
        proc.wait(timeout=5)

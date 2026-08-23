from pathlib import Path

def test_file_exists():
    assert Path("/workspace/result.txt").exists()

def test_content():
    assert Path("/workspace/result.txt").read_text().strip() == "42"

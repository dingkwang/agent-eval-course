from pathlib import Path

text = Path("result.txt").read_text()
assert text.strip() == "42", f"got {text!r}"

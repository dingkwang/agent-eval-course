#!/bin/bash
mkdir -p /workspace
cat > /workspace/sum.py <<'PY'
print(sum(int(l) for l in open("/workspace/numbers.txt") if l.strip()))
PY

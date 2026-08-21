#!/usr/bin/env bash
# Run one prediction file through the real SWE-bench evaluation harness.
#
#   bash labs/swe-bench-teardown/run.sh gold      # should resolve
#   bash labs/swe-bench-teardown/run.sh empty     # should NOT resolve
#   bash labs/swe-bench-teardown/run.sh broken    # patch fails to apply
#
# Experiment 3 (result caching): run the same run_id twice with different
# predictions and watch the harness reuse the cached result.
set -euo pipefail

KIND="${1:-gold}"
HERE="$(cd "$(dirname "$0")" && pwd)"
INSTANCE="${INSTANCE:-astropy__astropy-13398}"
RUN_ID="${RUN_ID:-teardown-$KIND}"

PRED="$HERE/preds_$KIND.jsonl"
[ -f "$PRED" ] || { echo "missing $PRED — run teardown.py first"; exit 1; }

echo "instance : $INSTANCE"
echo "prediction: $PRED"
echo "run_id   : $RUN_ID   ← 同一个 run_id 会命中缓存(实验 3)"
echo

# Use the CLONED repo (the one the lessons cite), not the older pip build.
REPO="$(cd "$HERE/../../../agent-sandbox-course/code/SWE-bench" && pwd)"
echo "harness   : $REPO/swebench/harness/run_evaluation.py"
echo

cd "$HERE"
PYTHONPATH="$REPO" python3 -m swebench.harness.run_evaluation \
  --dataset_name princeton-nlp/SWE-bench_Verified \
  --predictions_path "$PRED" \
  --instance_ids "$INSTANCE" \
  --run_id "$RUN_ID" \
  --max_workers 1 \
  --cache_level env \
  --timeout 1800

echo
echo "--- 产物 ---"
ls -1 "$HERE"/*.json 2>/dev/null | grep -i "teardown\|report" || true
find "$HERE/logs" -name "report.json" 2>/dev/null | head -3

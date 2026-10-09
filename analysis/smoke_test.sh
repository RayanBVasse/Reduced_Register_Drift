#!/usr/bin/env bash
# Confirms a fresh clone can reproduce the paper. Run from the repository root:
#   bash analysis/smoke_test.sh
set -u
cd "$(dirname "$0")/.." || exit 1
echo "Repository: $(pwd)"
for f in book_registry.json protocol_15q.json CondA1_Gemini_2.5Flash CondA2_Ungoverned_GPT4omini \
         CondA3_ScholarlyPrompt_GPT4omini CondB_Governed_GPT4omini; do
  [ -e "$f" ] && echo "  found    $f" || { echo "  MISSING  $f"; exit 1; }
done
n=$(find -L Cond*_* -name "*_Q*.json" | wc -l)
echo "  response files: $n (expect 600)"
[ "$n" -eq 600 ] || echo "  WARNING: expected 600 response files"
echo
echo "Running REPRODUCE_ALL.py ..."
python3 analysis/REPRODUCE_ALL.py > /tmp/rrd_repro.log 2>&1
rc=$?
grep -cE '^  PASS' /tmp/rrd_repro.log | xargs -I{} echo "  assertions passed: {}"
grep -cE '^  FAIL' /tmp/rrd_repro.log | xargs -I{} echo "  assertions failed: {}"
if [ $rc -eq 0 ]; then
  echo; echo "SMOKE TEST PASSED - every manuscript figure reproduces from the archived responses."
else
  echo; echo "SMOKE TEST FAILED - see /tmp/rrd_repro.log"; grep -E '^  FAIL' /tmp/rrd_repro.log
fi
exit $rc

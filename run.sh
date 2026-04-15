#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$(conda run -n agent which python)"

PROBLEM_FILE="${1:-$SCRIPT_DIR/problem/problem.tex}"
OUTPUT_DIR="${2:-$SCRIPT_DIR/proof_output}"
CONFIG="${3:-$SCRIPT_DIR/config.yaml}"

echo "============================================================"
echo "  Running smoke tests..."
echo "============================================================"
"$PYTHON" "$SCRIPT_DIR/code/smoke_test.py" --config "$CONFIG"
echo ""

# Copy global human_help into the output directory so the pipeline reads
# everything from proof_output.  Use cp -n to not overwrite files that
# already exist (e.g. edited by the UI before a resume).
mkdir -p "$OUTPUT_DIR/human_help"
for f in "$SCRIPT_DIR/human_help"/*; do
    [ -f "$f" ] && cp -n "$f" "$OUTPUT_DIR/human_help/" 2>/dev/null || true
done

echo "============================================================"
echo "  Proof Agent Pipeline"
echo "============================================================"
echo "  Problem:  $PROBLEM_FILE"
echo "  Output:   $OUTPUT_DIR"
echo "  Config:   $CONFIG"
echo ""

exec "$PYTHON" "$SCRIPT_DIR/code/pipeline.py" \
    --input "$PROBLEM_FILE" \
    --output "$OUTPUT_DIR" \
    --config "$CONFIG"

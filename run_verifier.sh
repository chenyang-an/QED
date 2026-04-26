#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

PROBLEM="${1:-$SCRIPT_DIR/standalone_verifier/problem.txt}"
PROOF="${2:-$SCRIPT_DIR/standalone_verifier/proof.txt}"
shift 2 2>/dev/null || true

OUTPUT_DIR="$SCRIPT_DIR/standalone_verifier_result"
mkdir -p "$OUTPUT_DIR"

python3 "$SCRIPT_DIR/verify/verify_proof.py" "$PROBLEM" "$PROOF" -o "$OUTPUT_DIR/report.md" "$@"

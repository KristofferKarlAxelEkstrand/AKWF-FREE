#!/usr/bin/env bash
# CI smoke build: one bank per target YAML definition.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BANK="${BANK:-AKWF_0001}"

echo "CI smoke build (bank: ${BANK})"
echo "=============================="

for yml in targets/*.yml; do
    base="$(basename "$yml")"
    echo
    echo ">>> ${base}"
    python3 scripts/convert.py --target "$yml" --bank "$BANK"
done

echo
echo "Smoke build complete. Validating outputs..."
python3 scripts/validate-built.py --bank "$BANK"

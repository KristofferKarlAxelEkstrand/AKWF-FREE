#!/usr/bin/env bash
# Verify repository formatting conventions (line endings, etc.)
# Usage: scripts/check-format.sh
# Exit 0 if clean, 1 if violations found.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

errors=0

echo "Checking line endings (expect LF, no CRLF)..."

# Text extensions to scan (skip binary and huge trees)
while IFS= read -r -d '' file; do
    if grep -q $'\r' "$file" 2>/dev/null; then
        echo "  CRLF: $file"
        errors=$((errors + 1))
    fi
done < <(find . \
    -path './.git' -prune -o \
    -path './src' -prune -o \
    -path './dist' -prune -o \
    -path './releases' -prune -o \
    -path './AKWF--*' -prune -o \
    -path './AKWF-js' -prune -o \
    -path './AKWF-c' -prune -o \
    -path './AKWF-png' -prune -o \
    -type f \( \
        -name '*.sh' -o -name '*.py' -o -name '*.yml' -o -name '*.yaml' \
        -o -name '*.json' -o -name '*.md' -o -name '*.txt' -o -name '*.toml' \
        -o -name '.editorconfig' -o -name '.gitattributes' -o -name '.prettierrc' \
        -o -name 'Dockerfile' -o -name 'Makefile' \
    \) -print0)

if [[ $errors -eq 0 ]]; then
    echo "  OK  no CRLF in project text files"
else
    echo
    echo "Found $errors file(s) with CRLF. Fix with:"
    echo "  sed -i 's/\\r\$//' <file>"
    echo "  git add --renormalize ."
    exit 1
fi

echo "Checking required config files..."
for f in .editorconfig .gitattributes; do
    if [[ -f $f ]]; then
        echo "  OK  $f"
    else
        echo "  MISSING  $f"
        errors=$((errors + 1))
    fi
done

if [[ $errors -gt 0 ]]; then
    exit 1
fi

echo "All format checks passed."

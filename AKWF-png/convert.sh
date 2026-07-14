#!/usr/bin/env bash
# Legacy wrapper — use the unified build system instead.
#   make build TARGET=targets/png-plots.yml
echo "Use: make build TARGET=targets/png-plots.yml" >&2
echo "Or:  python3 scripts/convert.py --target targets/png-plots.yml" >&2
exit 1

#!/usr/bin/env bash
# Legacy wrapper — use the unified build system instead.
#   make build TARGET=targets/teensy-c.yml
echo "Use: make build TARGET=targets/teensy-c.yml" >&2
echo "Or:  python3 scripts/convert.py --target targets/teensy-c.yml" >&2
exit 1

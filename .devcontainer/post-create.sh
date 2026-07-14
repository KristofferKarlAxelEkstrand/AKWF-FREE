#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo
echo '   _____   ____  __.__      _____________'
echo '  /  _  \ |    |/ _/  \    /  \_   _____/   F R E E'
echo ' /  /_\  \|      < \   \/\/   /|    __)'
echo '/    |    \    |  \ \        / |     \'
echo '\____|__  /____|__ \ \__/\  /  \___  /'
echo '        \/        \/      \/       \/'
echo
echo 'AKWF-FREE environment check'
echo '-----------------------------'

check_cmd() {
    local label="$1"
    shift
    if "$@" >/dev/null 2>&1; then
        printf '  OK  %-12s ' "$label"
        "$@" 2>/dev/null | head -n1
    else
        printf '  FAIL %-12s command not found or failed\n' "$label"
        exit 1
    fi
}

check_cmd Python     python3 --version
check_cmd SoX        sox --version
check_cmd gnuplot    gnuplot --version
check_cmd FFmpeg     ffmpeg -version

python3 - <<'PY'
import importlib

modules = ('numpy', 'scipy', 'soundfile', 'yaml', 'tqdm')
for name in modules:
    mod = importlib.import_module(name)
    version = getattr(mod, '__version__', 'unknown')
    print(f'  OK  {name:<12} {version}')
PY

if [[ ! -d src/AKWF ]]; then
    echo
    echo '  WARN source tree missing: src/AKWF/'
else
    count="$(find src/AKWF -name '*.wav' | wc -l | tr -d ' ')"
    echo
    echo "  OK  source       ${count} waveforms in src/AKWF/"
fi

echo
echo 'Format and build checks'
make check

echo
echo 'Ready. Quick start:'
echo '  make smoke                                              # CI-style test build'
echo '  make build TARGET=targets/akai-mpc.yml BANK=AKWF_0001   # single target'
echo

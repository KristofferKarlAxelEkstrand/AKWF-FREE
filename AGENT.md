# AGENT.md — AKWF-FREE Project Instructions

> Agent-agnostic project instructions. Any AI coding agent should read this file
> to understand the project, its structure, conventions, and how to work with it.

## Project Overview

**AKWF-FREE** (Adventure Kid Waveforms) is a CC0-licensed collection of **single-cycle waveforms** — the smallest meaningful audio sample of an instrument or sound source. These are single periods of a waveform stored as WAV files, designed to be looped seamlessly in synthesizers, samplers, and sound generators.

## Key Concepts

### Single-Cycle Waveforms

- A single-cycle waveform is exactly one period of a sound wave
- When looped continuously, it produces a sustained pitched tone
- The waveform shape determines the timbre/character of the sound
- These are NOT recordings — they are atomic tonal building blocks
- The first and last samples should seamlessly connect for gapless looping
- Length in samples determines resolution/quality, NOT pitch or duration

### Source Format (Canonical)

The source of truth lives in `src/AKWF/`:

- **Format:** WAV (PCM)
- **Length:** 600 samples per file
- **Bit depth:** 16-bit signed integer
- **Sample rate:** 44,100 Hz
- **Channels:** Mono
- **Peak level:** Normalized to ~0 dBFS (max amplitude near ±1.0)

The 600-sample length was chosen historically for layering octaves in an additive synth. It is NOT a standard power-of-2 buffer size but is the canonical source from which all other formats are derived.

### Targets

Each target is a format conversion optimized for a specific synthesizer, sampler, platform, or use case. Targets may differ in:

- Sample length (64, 256, 512, 1024, 2048)
- Bit depth (16-bit, 24-bit, 32-bit float)
- Sample rate (44.1kHz, 48kHz, 96kHz)
- File format (WAV, RAW, C header, JSON, PNG, synth-specific patches)
- File naming conventions (lowercase .wav vs uppercase .WAV)
- Folder structure requirements
- Normalization level
- Additional metadata or headers

## Project Structure

```
AKWF-FREE/
├── AGENT.md                    # This file — project instructions for agents
├── PROJECT-DESCRIPTION.md      # Full project plan and roadmap
├── README.md                   # Public-facing documentation
├── LICENSE.md                  # CC0 1.0 Universal
│
├── src/
│   └── AKWF/                   # CANONICAL SOURCE — do not modify generated files here
│       ├── AKWF_0001/         # Numbered banks (generic waveforms)
│       │   ├── AKWF_0001.wav
│       │   ├── AKWF_0002.wav
│       │   └── ...
│       ├── AKWF_aguitar/      # Named banks (instrument-specific)
│       ├── AKWF_cello/
│       └── ...                # ~4358 waveforms across 65 banks
│
├── targets/                    # Target definitions
│   ├── README.md              # Target definition schema & docs
│   ├── akwf-standard.yml      # Matrix: all power-of-2 × bit depth × SR combos
│   ├── akai-mpc.yml           # Akai MPC sampler format
│   ├── surge-1024.yml         # Surge synth 1024-sample wavetables
│   ├── surge-512.yml          # Surge synth 512-sample wavetables
│   ├── teensy-c.yml           # Teensy C header arrays
│   ├── web-json.yml           # JSON for web players
│   └── png-plots.yml          # PNG waveform visualizations
│
├── scripts/                    # Build/conversion tooling
│   ├── convert.py             # Main conversion engine
│   ├── targets.py             # Shared target-YAML loading/matrix expansion
│   ├── validate.py            # Output quality validation
│   ├── validate-built.py      # Validate all dist/ outputs
│   ├── package.py             # Zip packaging for releases
│   ├── check-format.sh        # Line-ending and config checks
│   └── ci-smoke.sh            # CI one-bank-per-target build
│
├── Makefile                    # check, smoke, build, validate, package, clean
├── requirements.txt            # Pinned Python dependencies
├── .github/workflows/ci.yml    # GitHub Actions CI
│
├── dist/                       # Built outputs (gitignored, generated)
│   ├── AKWF--64smp-16bit-44_1k/
│   ├── AKWF--1024smp-32bit-48k/
│   ├── AKWF--Akai-MPC/
│   └── ...
│
├── releases/                   # Zip archives (gitignored)
│
├── AKWF--*/                    # Legacy pre-built outputs (to be migrated to dist/)
├── AKWF-c/                     # Legacy C headers (regenerate via targets/teensy-c.yml)
├── AKWF-js/                    # Legacy JSON (regenerate via targets/web-json.yml)
└── AKWF-png/                   # Legacy PNG plots (regenerate via targets/png-plots.yml)
```

## Working With This Project

### Building Targets

Use the Makefile (recommended) or run scripts directly.

```bash
make check                                              # format checks + list targets
make smoke                                              # one bank per target (CI)
make build TARGET=targets/akai-mpc.yml BANK=AKWF_0001   # single target
make build                                              # full library (slow)
make validate                                           # validate built outputs
make package                                            # zip to releases/
make clean                                              # remove dist/ and releases/
```

Or directly:

```bash
python3 scripts/convert.py --target targets/akwf-standard.yml --bank AKWF_0001
python3 scripts/convert.py --all
python3 scripts/convert.py --list
```

**Dependencies:** `pip install -r requirements.txt`

### Adding a New Target

**Single target:** Create a YAML file in `targets/`:

```yaml
name: "Akai MPC"
output_dir: "AKWF--Akai-MPC"
description: "Format compatible with Akai MPC samplers"

audio:
  format: wav                 # wav | raw | c-header | json | png | custom
  bit_depth: 16                # 8 | 16 | 24 | 32 (32 = float)
  sample_rate: 44100
  channels: mono              # mono | stereo (stereo duplicates the mono signal to both channels)
  length_samples: 600

resample:
  method: none               # none | sinc | linear | sox-speed | sox-rate
  quality: high               # low | medium | high | very-high — only affects sox-rate

normalize:
  enabled: true
  method: peak               # peak | gain
  target_dbfs: -0.1
  gain_db: -6.4               # used when method is gain (legacy SoX `gain` parity, e.g. Surge targets)
  remove_dc: true

naming:
  extension: ".WAV"
  filename_case: preserve    # preserve | upper | lower
  extension_case: upper      # lower | upper

structure:
  mirror_source: true

metadata:
  add_loop_points: true

packaging:
  zip: true
  zip_name: "AKWF--Akai-MPC.zip"

skip:
  banks: ["AKWF_stereo"]
```

**Matrix target:** Use `type: matrix` for combinations:

```yaml
type: matrix

matrix:
  length_samples: [64, 128, 256, 512, 1024, 2048]
  bit_depth: [16, 32]
  sample_rate: [44100, 48000]

defaults:
  # Same fields as single target — applied to all combinations

output_template:
  dir: "AKWF--{length}smp-{bits}bit-{rate_k}k"
  zip: "AKWF--{length}smp-{bits}bit-{rate_k}k.zip"
  name: "AKWF {length}smp {bits}-bit {rate_k}kHz"
```

### Resampling

- **FFT-based sinc** (`scipy.signal.resample`) — default, mathematically optimal for periodic signals
- Treats signal as periodic (exactly what single-cycle waveforms are)
- Preserves all harmonics below Nyquist with zero aliasing
- Output is perfectly loopable
- All processing in 64-bit float internally
- **sox-rate** (legacy Teensy AKWF-c approach) resamples via SoX's `rate` effect; `resample.quality` maps to SoX's quality presets here (no-op for `sinc`/`linear`/`sox-speed`)
- **sox-speed** (legacy AKWF--Surge approach) resamples via SoX's `speed` factor for bit-exact legacy parity

### Dithering

- **TPDF** (Triangular Probability Density Function) applied when quantizing to 8-bit, 16-bit, or 24-bit — `wav`/`raw` formats only
- Decorrelates quantization error, replacing distortion with a tiny noise floor
- 32-bit float output skips dithering
- `c-header` output is never dithered — it quantizes straight to `uint16` via `float_to_uint16()`, not through the wav/raw dither path

### Validation

`scripts/validate.py` dispatches by output format (wav/raw/json/c-header/png), auto-detected from the directory contents or read from `--target`:

```bash
python3 scripts/validate.py dist/AKWF--1024smp-16bit-44_1k/
python3 scripts/validate.py dist/AKWF--1024smp-16bit-44_1k/ --target targets/akwf-standard.yml
```

`scripts/validate-built.py` (what `make validate` runs) does the same across every target in `dist/` at once.

### Packaging

```bash
python3 scripts/package.py --target targets/akwf-standard.yml
python3 scripts/package.py --all
```

### Release Process

1. `make build` — build all targets to `dist/`
2. `make validate` — verify outputs
3. `make package` — create zip archives in `releases/`
4. Tag the commit on `master`
5. Upload zips as GitHub release assets

## Conventions

- Source files in `src/AKWF/` are NEVER modified by build scripts
- All generated output goes to `dist/`
- File names preserve the `AKWF_` prefix
- Bank folder names preserve the `AKWF_` prefix
- One waveform = one file = one single cycle
- The `AKWF_stereo` bank is special (stereo files) — skip or handle per target
- Output naming: `AKWF--{length}smp-{bits}bit-{rate_k}k` (double-dash prefix)
- Rate uses underscore: `44_1k` not `44.1k` (dots in filenames cause issues)

## Important Notes

- The source is 600 samples — an unusual, non-power-of-2 length by historical design
- The collection has ~4358 mono waveforms across 65 banks
- License is CC0 — completely public domain, no attribution required
- The project currently lives on the `updates` branch; `master` is the default/release branch

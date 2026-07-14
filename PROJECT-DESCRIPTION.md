# PROJECT-DESCRIPTION.md — AKWF-FREE Build System Plan

## What This Project Is

AKWF-FREE is a library of **single-cycle waveforms** — atomic sound building blocks used in synthesizers and samplers worldwide. The source collection contains ~4358 waveforms at 600 samples / 16-bit / 44.1kHz / mono. These need to be converted into multiple formats for different hardware and software targets.

## Current State

### Source (`src/AKWF/`)
- 65 banks of waveforms (20 numbered + 45 named by instrument/type)
- 600 samples, 16-bit PCM, 44100 Hz, mono WAV
- Peak normalized (most files near 0 dBFS)
- This is the ground truth — everything else is derived from here

### Existing Targets (already in repo)
| Target | Format | Length | Bit Depth | Sample Rate | Notes |
|--------|--------|--------|-----------|-------------|-------|
| Akai MPC | .WAV | 600 | 16-bit | 44100 | Same specs, different WAV headers/metadata |
| Surge 1024 | .wav | 1024 | 16-bit | 44100 | Resampled via SoX speed |
| Surge 512 | .wav | 512 | 16-bit | 44100 | Resampled via SoX speed |
| Surge 64 | .wav | 64 | 16-bit | 44100 | Heavily downsampled |
| Surge WT | .wt | 512 | 16-bit | 44100 | Wavetable format |
| Teensy (C) | .h | 256 | 16-bit unsigned | N/A | C arrays for embedded |
| Web (JS) | .json | 600 | float | N/A | Normalized -1.0 to 1.0 |
| PNG | .png | N/A | N/A | N/A | Visual plots |
| Big-Tick Rhino | .add | ? | ? | ? | Additive synth patches |
| U-he Zebra | .h2p | N/A | N/A | N/A | Zebra preset format |
| Alchemy | .raw | ? | ? | ? | LFO waveforms |

### Existing Tools
- `AKWF-c/convert.sh` — SoX + hexdump to C headers (resamples to 256 via rate change)
- `AKWF-js/convert.py` — Python WAV-to-JSON (reads 16-bit, outputs normalized floats)
- `AKWF-png/convert.sh` — SoX + gnuplot to PNG visualizations
- `AKWF--Surge/README.md` — Documents SoX `speed` approach for resampling

## Planned Architecture

### Directory Structure

```
AKWF-FREE/
├── AGENT.md                        # Agent instructions
├── PROJECT-DESCRIPTION.md          # This file
├── README.md                       # Public documentation
├── LICENSE.md                      # CC0 1.0
├── Makefile                        # Build orchestration
├── requirements.txt                # Pinned Python dependencies
├── .github/workflows/ci.yml        # GitHub Actions CI
│
├── src/
│   └── AKWF/                       # CANONICAL SOURCE
│       ├── AKWF_0001/
│       │   ├── AKWF_0001.wav      # 600 samples, 16-bit, 44.1kHz, mono
│       │   └── ...
│       ├── AKWF_aguitar/
│       ├── AKWF_cello/
│       └── ... (65 banks, ~4358 files)
│
├── targets/                        # Target definitions
│   ├── README.md                   # How to write a target definition
│   ├── akwf-standard.yml           # Matrix: all power-of-2 × bit depth × SR
│   ├── akai-mpc.yml
│   ├── surge-1024.yml
│   ├── surge-512.yml
│   ├── teensy-c.yml
│   ├── web-json.yml
│   └── png-plots.yml
│
├── scripts/                        # Conversion engine
│   ├── convert.py                  # Main build script
│   ├── validate.py                 # Single-directory validation
│   ├── validate-built.py           # Validate all dist/ outputs
│   ├── package.py                  # Zip packaging for releases
│   ├── check-format.sh             # Line-ending and config checks
│   └── ci-smoke.sh                 # CI one-bank-per-target build
│
├── dist/                           # Build output (gitignored)
│   ├── AKWF--64smp-16bit-44_1k/
│   ├── AKWF--2048smp-32bit-48k/
│   ├── AKWF--Akai-MPC/
│   └── ...
│
└── releases/                       # Zip archives (gitignored)
    ├── AKWF--64smp-16bit-44_1k.zip
    ├── AKWF--2048smp-32bit-48k.zip
    └── ...
```

### Target Definition Format

Each `.yml` file in `targets/` fully describes how to build one output format.
Matrix targets (with `type: matrix`) expand into multiple individual configs.

```yaml
# Single target example
name: "Akai MPC"
output_dir: "AKWF--Akai-MPC"
description: "Format compatible with Akai MPC samplers"

audio:
  format: wav
  bit_depth: 16
  sample_rate: 44100
  channels: mono
  length_samples: 600

resample:
  method: none               # none | sinc | linear | sox-speed | sox-rate

normalize:
  enabled: true
  method: peak               # peak | gain
  target_dbfs: -0.1
  remove_dc: true

naming:
  extension: ".WAV"
  filename_case: preserve    # preserve | upper | lower
  extension_case: upper

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

### Conversion Pipeline

For each target, the build system does:

```
1. READ source     → Load 600-sample 16-bit WAV from src/AKWF/
2. DECODE          → Convert to 64-bit float internally (no precision loss)
3. REMOVE DC       → Center waveform around zero
4. RESAMPLE        → FFT-based sinc interpolation to target length
5. NORMALIZE       → Peak normalize to target dBFS level
6. DITHER          → TPDF dither for 8/16/24-bit wav/raw output (c-header skips this — quantizes straight to uint16)
7. WRITE           → Output to dist/<target>/ with correct naming/structure
```

### Resampling Strategy

- **FFT-based sinc** (`scipy.signal.resample`) — mathematically optimal for periodic signals
- Treats the 600 samples as one period of a periodic signal
- Zero-pads or truncates in frequency domain
- Preserves all harmonics below Nyquist with zero aliasing
- Output is perfectly loopable (periodicity is inherent in the method)

**SoX approach (simpler, slightly lower quality):**
- `sox input.wav output.wav speed <factor>` where factor = 600/target_length
- Quick and works for most use cases
- May introduce very slight loop discontinuity at boundaries

### Normalization Strategy

- **Peak normalization** (default): Scale so the maximum absolute sample value = target level
- **Target:** -0.1 dBFS for safety (avoids intersample overs on some DACs)
- **Per-file:** Each waveform normalized independently
- **Fixed gain** (`method: gain`, `gain_db`): applies a constant dB gain instead of peak-normalizing — used for legacy SoX parity (e.g. Surge targets)

### Quality Considerations

| Concern | Solution |
|---------|----------|
| Loop continuity | FFT resampling preserves periodicity; validate first/last sample match |
| Aliasing | Band-limited interpolation; never upsample without proper filtering |
| Quantization noise | Work in 64-bit float internally, dither when going to 16/24-bit |
| DC offset | Remove DC offset before normalization |
| Intersample overs | Normalize to -0.1 dBFS, not 0 dBFS |

## Tooling

### Required
- **Python 3.11+** — Build orchestration, YAML parsing, custom formats
- **SoX 14.4+** — Alternative resampling for C-header targets (already installed)
- **FFmpeg 5+** — Format probing, edge cases (already installed)

### Python Dependencies (install via pip)
- `numpy` — Array operations, float processing
- `scipy` — `scipy.signal.resample` for FFT-based resampling
- `soundfile` — Read/write WAV at various bit depths (wraps libsndfile)
- `pyyaml` — Parse target definitions
- `tqdm` — Progress bars for batch operations

## Release Strategy

### Git Tags & GitHub Releases
1. Build all targets on `master` branch
2. Create zips per target: `AKWF--<TargetName>.zip`
3. Tag as `vX.Y.Z` (semantic versioning)
4. Create GitHub Release with:
   - Release notes (what changed)
   - All target zips as downloadable assets
   - The source collection zip (`src/AKWF.zip`)

### Versioning
- Major: New waveforms added or removed from source
- Minor: New targets added
- Patch: Build fixes, target definition tweaks

## Implementation Roadmap

### Phase 1: Foundation ✱ (current)
- [x] Research project structure and formats
- [x] Create AGENT.md
- [x] Create PROJECT-DESCRIPTION.md
- [x] Move source to `src/AKWF/`
- [x] Create `targets/` directory with README
- [x] Create target definitions (matrix + individual)
- [x] Set up `scripts/convert.py` with FFT resampling + TPDF dither
- [x] Set up `scripts/validate.py` for output verification
- [x] Set up `scripts/package.py` for zip packaging
- [x] Add `.gitignore` for `dist/` and `releases/`

### Phase 2: Core Engine
- [x] Implement FFT-based sinc resampling
- [x] Implement peak normalization with DC removal
- [x] Implement TPDF dithering for integer formats
- [x] Implement validation (loop check, level check, DC check)
- [x] Test with one bank, all targets

### Phase 3: All Targets
- [x] Define standard matrix target (24 variants)
- [x] Define Akai MPC target
- [x] Define Surge targets
- [x] Define Teensy C header target
- [x] Define web JSON target
- [x] Define PNG plots target
- [ ] Migrate existing target outputs to be generated
- [ ] Verify parity with existing converted files

### Phase 4: Release
- [x] Implement zip packaging
- [x] Set up GitHub Actions for automated builds
- [ ] Create first tagged release with all assets
- [ ] Update README with download links

## Notes

- The `AKWF_stereo` bank contains stereo files — handle specially (skip or convert to mono)
- Some targets (Zebra .h2p, Rhino .add) are synth-specific patch formats that may need reverse engineering or manual creation
- The existing `AKWF--*` folders in the repo currently hold pre-built outputs — these will eventually be replaced by `dist/` outputs
- The `AKWF-c/`, `AKWF-js/`, `AKWF-png/` folders are code/visualization formats, not audio targets per se

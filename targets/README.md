# Target Definitions

Each `.yml` file in this directory defines a conversion target — a specific output format for a synthesizer, sampler, platform, or use case.

## How It Works

The build system reads a target definition and converts every waveform in `src/AKWF/` according to the specified parameters. Output goes to `dist/<output_dir>/`.

## Schema

```yaml
name: "Human-readable name"
output_dir: "AKWF--Output-Folder-Name"
description: "What this target is for"

audio:
  format: wav              # wav | raw | c-header | json | png | custom
  bit_depth: 16            # 8 | 16 | 24 | 32 (32 = float)
  sample_rate: 44100       # 44100 | 48000 | 96000
  channels: mono           # mono | stereo (stereo duplicates to both channels)
  length_samples: 600      # Target cycle length in samples

resample:
  method: sinc             # sinc | linear | sox-speed | sox-rate | none
  quality: very-high       # low | medium | high | very-high
  # 'none' means no resampling (source is already correct length)
  # 'sinc' uses FFT-based resampling (best for periodic signals)
  # 'sox-speed' uses SoX `speed` factor (600/target_length) — legacy Surge
  # 'sox-rate' uses SoX sample-rate change — legacy Teensy C headers

normalize:
  enabled: true
  method: peak             # peak | gain
  target_dbfs: -0.1        # Target level in dBFS (0.0 = max, negative = headroom)
  gain_db: -6.4            # Fixed gain when method is gain (legacy SoX parity)
  remove_dc: true          # Remove DC offset before normalizing

naming:
  extension: ".wav"        # File extension including dot
  filename_case: preserve  # preserve | upper | lower
  extension_case: lower    # lower | upper

structure:
  mirror_source: true      # true = replicate bank folder layout from src/AKWF
  flat: false              # true = all files in one directory (no bank folders)

metadata:
  add_loop_points: false   # Add WAV smpl chunk with loop start=0, end=length-1

packaging:
  zip: true
  zip_name: "auto"         # 'auto' uses output_dir name, or specify custom name

skip:
  banks: []                # List of bank names to skip (e.g., ["AKWF_stereo"])
```

## Fields Reference

### `audio.format`
- `wav` — Standard PCM WAV file
- `raw` — Raw PCM data, no headers
- `c-header` — C/C++ header with uint16 array (for embedded/Teensy)
- `json` — JSON arrays of normalized floats (-1.0 to 1.0)
- `png` — Waveform plot images
- `custom` — Target-specific handler (must implement in scripts)

### `resample.method`
- `sinc` — FFT-based resampling. Treats signal as periodic, zero-pads/truncates spectrum. Perfect for single-cycle waveforms. Requires scipy.
- `sox-speed` — Uses SoX `speed` factor (600/target_length). Legacy Surge parity.
- `sox-rate` — Uses SoX sample-rate change. Legacy Teensy C-header parity.
- `linear` — Linear interpolation. Fast but lower quality (okay for large downsamples like 600→64).
- `none` — No resampling. Only valid when target length = 600.

### `resample.quality`
Only affects `sox-rate` (mapped to SoX's `rate` effect quality presets: `quick`/`low`/`medium`/`high`/`very-high`). `sinc` resampling is exact (no quality knob to tune), `linear` has no quality parameter, and `sox-speed` must stay bit-for-bit with the legacy SoX `speed` command for parity — `quality` is a no-op for all three.

### `normalize.target_dbfs`
- `0.0` — Peak hits exactly ±1.0 (maximum level, may cause intersample overs)
- `-0.1` — Safe maximum (recommended for most targets)
- `-1.0` — 1 dB headroom
- `-3.0` — Conservative headroom
- `-6.0` — Significant headroom (useful for mixing contexts)

### `normalize.method: gain`
- Applies fixed gain in dB (`gain_db`), matching legacy SoX `gain` (e.g. Surge targets use `-6.4`)

## Adding a Target

**Single target:** Copy an existing `.yml` as a starting point, adjust parameters, then:
```bash
python3 scripts/convert.py --target targets/your-target.yml
python3 scripts/validate.py dist/Your-Output-Dir/
```

**Matrix target:** Use `type: matrix` to define combinations of length × bit depth × sample rate. See `akwf-standard.yml` for the pattern. The build script expands these automatically.

## Tips

- For synthesizers that expect power-of-2 lengths: use 256, 512, 1024, or 2048
- For hardware samplers with file naming restrictions: check `naming` options
- If your target needs a custom format not covered by the schema, use `format: custom` and implement a handler in `scripts/`
- Always test with a small subset first before running the full library

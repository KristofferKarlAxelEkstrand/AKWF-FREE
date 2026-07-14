# AKWF

```text
   _____   ____  __.__      _____________
  /  _  \ |    |/ _/  \    /  \_   _____/   F R E E
 /  /_\  \|      < \   \/\/   /|    __)
/    |    \    |  \ \        / |     \
\____|__  /____|__ \ \__/\  /  \___  /
        \/        \/      \/       \/
```

AKWF or Adventure Kid Waveforms is a collection of one cycle waveforms
to be used within synthesizers or other kinds of sound generators. It
is basically the smallest sound possible to sample and still get the
overall feel of the sampled instrument.

## Building

Canonical source waveforms live in `src/AKWF/` (600 samples, 16-bit, 44.1 kHz, mono).
The build system converts them into platform-specific formats defined in `targets/*.yml`.

### Dev container (recommended)

1. Open the repo in VS Code / Cursor and **Reopen in Container**
2. On first create, `.devcontainer/post-create.sh` verifies tools and runs smoke checks
3. Rebuild after Dockerfile changes: **Dev Containers: Rebuild Container**

Installed in the container: Python 3.11, SoX, gnuplot, FFmpeg, and pinned packages from `requirements.txt`.

### Local setup

**System dependencies:** SoX, gnuplot, FFmpeg, libsndfile

```bash
# Debian/Ubuntu
sudo apt-get install sox libsox-fmt-all gnuplot ffmpeg libsndfile1

# Python dependencies
pip install -r requirements.txt
```

### Make targets

```bash
make check                  # line-ending checks + list targets
make smoke                  # build one bank per target (CI default)
make build TARGET=targets/akai-mpc.yml BANK=AKWF_0001
make build                  # full library build (slow)
make validate BANK=AKWF_0001
make package                # zip dist/ outputs to releases/
make clean                  # remove dist/ and releases/

```
## Code Style

The repository uses **pre‑commit** to enforce consistent formatting for Python, C/C++, Markdown, JSON, YAML, and other files.

- Install hooks: `pre-commit install`
- Run formatting locally: `make format` or `pre-commit run --all-files`
- The CI job also runs these checks.
```

Or directly:

```bash
python3 scripts/convert.py --list
python3 scripts/convert.py --target targets/akai-mpc.yml --bank AKWF_0001
python3 scripts/validate-built.py --bank AKWF_0001
python3 scripts/package.py --all
```

Outputs go to `dist/`. Release zips go to `releases/`.

### Generated targets

| Target YAML | Output | Format |
|-------------|--------|--------|
| `akai-mpc.yml` | `AKWF--Akai-MPC/` | 600-sample WAV (.WAV) |
| `surge-512.yml`, `surge-1024.yml` | `AKWF--Surge/` | 512/1024-sample WAV |
| `akwf-standard.yml` | 24 matrix variants | 64–2048 samples, 16/32-bit, 44.1/48 kHz |
| `teensy-c.yml` | `AKWF-c/` | C headers (256 samples) |
| `web-json.yml` | `AKWF-js/` | JSON float arrays |
| `png-plots.yml` | `AKWF-png/` | PNG waveform plots |

Pre-built `AKWF--*` folders in the repo are legacy outputs. Regenerate them with `make build`.

The `AKWF_stereo` bank (200 stereo files) is skipped by all targets.

## Versions

### AKWF (Original)

The waveforms are 600 samples long, chosen during my early work on
an additive synth in high school. That length worked well for
layering octaves, while shorter cycles degraded the sound. I hadn’t
yet learned about standard buffer sizes like 256 or 1024—this was
just my starting point.

If you use it as a sample and treat it as a C and pitch it to D1+2,
you get an actual C... yeah... I know...

- File format: Wave
- Length: 600 samples
- Bit depth: 16bit
- Sample rate: 44.1khz
- Channels: Mono

### AKWF--Akai-MPC

- File format: Wave
- Length:
- Bit depth: 16bit
- Sample rate: 44.1khz
- Channels: Mono

### AKWF--Alchemy--Camel-Audio

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Big-Tick-Rhino

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Corona-Discovery-Pro

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Elektron--Model Samples

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--MonoMachine-SFX-60+

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Music-Line--Amiga

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Pro-Tracker--ST-Clones

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Reaktor

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--SonicWare--Smpltrek

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Surge

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Synapse-Audio-DUNE-3

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Synthesis-Technology

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--Teensy

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--TX16W-Typhoon-Cyclone

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--U-he-Zebra

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF--WT--Harmor-Komplexer

- File format:
- Length:
- Bit depth:
- Sample rate:
- Channels:

### AKWF-c

The waveforms are defined in C as arrays of 16 unsigned integers, so basically 16-bit data.

- File format: Array
- Length: XX
- Bit depth: 16bit
- Sample rate: N/A
- Channels: Mono

### AKWF-js

JSON arrays of normalized floating-point samples for web players and Web Audio API.

- File format: JSON
- Length: 600 values per waveform
- Bit depth: N/A (float, 6 decimal places)
- Sample rate: N/A
- Channels: Mono

### AKWF-png

View AKWF waveforms as PNG plots for visual reference. Each image offers a straightforward depiction of the waveform shape to aid analysis and selection.

### Listening

There is an [open source app](https://github.com/tashian/waves) for previewing the waveforms.
See [AKWF Player](https://waves.tashian.com).

### Sound-generators

#### [QU-Bit Chord](https://www.qubitelectronix.com/)

Chord is a plug and play solution for bringing musical polyphony to your modular system. In the Qubit Chord module, AKWF (Adventure Kid Waveforms) provide textures, allowing for creative sound design in modular synthesis. Ideal for adding complex and evolving tones.

#### [Elektron Model:Samples](https://elektron.se/explore/modelsamples)

Elektron Model:Samples uses AKWF in it's sound library.

## Usage

These waveforms are compact, single-cycle samples used as oscillator shapes. They can be loaded into samplers as pitch-tuned sources or into synthesizers as static waveform options. While not wavetables, some synths allow morphing between them. Their low resource demands make them suitable for both old gear and more modern setups, offering a bit more timbral variety beyond the basic shapes for synthesizers and enabling some kind of hybrid synth-sampler behavior.

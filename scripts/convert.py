#!/usr/bin/env python3
"""
AKWF-FREE Conversion Engine

Converts source waveforms from src/AKWF/ to target formats defined in targets/*.yml.

Usage:
    python3 scripts/convert.py --target targets/akai-mpc.yml
    python3 scripts/convert.py --target targets/akai-mpc.yml --bank AKWF_0001
    python3 scripts/convert.py --target targets/akai-mpc.yml --dry-run
    python3 scripts/convert.py --all
    python3 scripts/convert.py --list

Requirements:
    pip install -r requirements.txt
    System: SoX, gnuplot
"""

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml

from targets import expand_matrix, load_target

try:
    from scipy.signal import resample as scipy_resample
except ImportError:
    scipy_resample = None

try:
    import soundfile as sf
except ImportError:
    sf = None

try:
    from tqdm import tqdm
except ImportError:

    def tqdm(iterable, **kwargs):
        return iterable


ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src" / "AKWF"
DIST_DIR = ROOT / "dist"
TARGETS_DIR = ROOT / "targets"


def get_source_banks(skip_banks=None):
    """Get list of source bank directories."""
    if not SRC_DIR.exists():
        print(f"ERROR: Source directory not found: {SRC_DIR}", file=sys.stderr)
        sys.exit(1)

    banks = sorted(d for d in SRC_DIR.iterdir() if d.is_dir())
    if skip_banks:
        banks = [b for b in banks if b.name not in skip_banks]
    return banks


# ---------------------------------------------------------------------------
# Signal processing
# ---------------------------------------------------------------------------


def read_source_samples(source_path):
    """Read source WAV as mono float64 in -1.0..1.0 range."""
    if sf is None:
        print(
            "ERROR: soundfile required. Install: pip install soundfile", file=sys.stderr
        )
        sys.exit(1)

    samples, _ = sf.read(str(source_path), dtype="float64")
    if len(samples.shape) > 1:
        samples = samples[:, 0]
    return samples


def resample_sinc(samples, target_length):
    """FFT-based resampling for periodic single-cycle waveforms."""
    if scipy_resample is None:
        print("ERROR: scipy required for sinc resampling.", file=sys.stderr)
        sys.exit(1)

    return scipy_resample(np.array(samples, dtype=np.float64), target_length)


def resample_linear(samples, target_length):
    """Linear interpolation resampling."""
    x_old = np.linspace(0, 1, len(samples), endpoint=False)
    x_new = np.linspace(0, 1, target_length, endpoint=False)
    return np.interp(x_new, x_old, samples)


SOX_RATE_QUALITY_FLAGS = {
    "quick": "-q",
    "low": "-l",
    "medium": "-m",
    "high": "-h",
    "very-high": "-v",
}


def resample_sox_rate(source_path, target_length, quality=None):
    """Resample using SoX sample-rate change (legacy Teensy AKWF-c approach).

    Always returns signed float64 samples in -1..1 range — normalize/remove_dc
    are applied afterward by process_samples(), same as every other resample method.
    """
    if sf is None:
        print("ERROR: soundfile required.", file=sys.stderr)
        sys.exit(1)

    info = sf.info(str(source_path))
    target_sr = int(info.samplerate * target_length / info.frames)

    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tmp:
        tmp_path = tmp.name

    rate_effect = ["rate"]
    if quality in SOX_RATE_QUALITY_FLAGS:
        rate_effect.append(SOX_RATE_QUALITY_FLAGS[quality])
    rate_effect.append(str(target_sr))

    try:
        subprocess.run(
            ["sox", str(source_path), "-e", "signed", tmp_path] + rate_effect,
            check=True,
            capture_output=True,
        )
        data = np.fromfile(tmp_path, dtype=np.int16)
        return data.astype(np.float64) / 32768.0
    except FileNotFoundError:
        print(
            "ERROR: sox not found. Install SoX for sox-speed resampling.",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: sox failed: {e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def resample_sox_speed(source_path, target_length):
    """Resample using SoX speed factor (legacy AKWF--Surge approach).

    Factor = source_length / target_length (e.g. 600/1024 = 0.5859).
    """
    if sf is None:
        print("ERROR: soundfile required.", file=sys.stderr)
        sys.exit(1)

    info = sf.info(str(source_path))
    factor = info.frames / target_length

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        output_path = tmp_path / "out.wav"
        try:
            subprocess.run(
                ["sox", str(source_path), str(output_path), "speed", f"{factor:.6f}"],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            print(
                "ERROR: sox not found. Install SoX for sox-speed resampling.",
                file=sys.stderr,
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            print(f"ERROR: sox failed: {stderr}", file=sys.stderr)
            sys.exit(1)

        samples, _ = sf.read(str(output_path), dtype="float64")
        if len(samples.shape) > 1:
            samples = samples[:, 0]
        return samples


def normalize_peak(samples, target_dbfs=-0.1):
    """Peak normalize to target dBFS level."""
    target_linear = 10 ** (target_dbfs / 20.0)
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples * (target_linear / peak)
    return samples


def normalize_gain(samples, gain_db):
    """Apply fixed gain in dB (legacy SoX `gain` parity)."""
    return samples * (10 ** (gain_db / 20.0))


def remove_dc_offset(samples):
    """Remove DC offset."""
    return samples - np.mean(samples)


def process_samples(samples, config, source_path=None):
    """Apply DC removal, resample, and peak normalization."""
    samples = np.array(samples, dtype=np.float64)

    audio_config = config.get("audio", {})
    resample_config = config.get("resample", {})
    normalize_config = config.get("normalize", {})

    if normalize_config.get("remove_dc", False):
        samples = remove_dc_offset(samples)

    target_length = audio_config.get("length_samples")
    if target_length and target_length != len(samples):
        method = resample_config.get("method", "sinc")
        if method == "sinc":
            samples = resample_sinc(samples, target_length)
        elif method == "linear":
            samples = resample_linear(samples, target_length)
        elif method == "sox-speed":
            if source_path is None:
                print("ERROR: sox-speed requires source file path.", file=sys.stderr)
                sys.exit(1)
            samples = resample_sox_speed(source_path, target_length)
        elif method == "sox-rate":
            if source_path is None:
                print("ERROR: sox-rate requires source file path.", file=sys.stderr)
                sys.exit(1)
            samples = resample_sox_rate(
                source_path,
                target_length,
                quality=resample_config.get("quality"),
            )
        elif method != "none":
            print(f"ERROR: Unknown resample method: {method}", file=sys.stderr)
            sys.exit(1)

    if normalize_config.get("enabled", False):
        norm_method = normalize_config.get("method", "peak")
        if norm_method == "gain":
            gain_db = normalize_config.get("gain_db")
            if gain_db is None:
                print(
                    "ERROR: normalize.method 'gain' requires gain_db.", file=sys.stderr
                )
                sys.exit(1)
            samples = normalize_gain(samples, gain_db)
        else:
            target_dbfs = normalize_config.get("target_dbfs", -0.1)
            samples = normalize_peak(samples, target_dbfs)

    return samples


def load_samples(source_path, config):
    """Read and process source samples according to target config."""
    samples = read_source_samples(source_path)
    return process_samples(samples, config, source_path=source_path)


def dither_rng_for_file(source_path):
    """Deterministic RNG for TPDF dither (seeded from source path)."""
    seed = int(hashlib.sha256(str(source_path).encode()).hexdigest()[:16], 16)
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# WAV loop points
# ---------------------------------------------------------------------------


def add_smpl_loop_to_wav(wav_path, loop_start=0, loop_end=None):
    """Insert or replace a WAV smpl chunk with a single forward loop."""
    wav_path = Path(wav_path)

    with open(wav_path, "rb") as f:
        if f.read(4) != b"RIFF":
            raise ValueError(f"Not a RIFF file: {wav_path}")
        riff_size = struct.unpack("<I", f.read(4))[0]
        if f.read(4) != b"WAVE":
            raise ValueError(f"Not a WAVE file: {wav_path}")

        chunks = []
        while f.tell() < 8 + riff_size:
            chunk_id = f.read(4)
            if len(chunk_id) < 4:
                break
            chunk_size = struct.unpack("<I", f.read(4))[0]
            chunk_data = f.read(chunk_size)
            if chunk_size % 2:
                f.read(1)
            if chunk_id != b"smpl":
                chunks.append((chunk_id, chunk_data))

    if loop_end is None:
        for chunk_id, chunk_data in chunks:
            if chunk_id == b"data":
                loop_end = (len(chunk_data) // 2) - 1
                break
        if loop_end is None:
            raise ValueError(f"Cannot determine loop end for {wav_path}")

    smpl_body = struct.pack("<9I", 0, 0, 0, 60, 0, 0, 0, 1, 0)
    smpl_body += struct.pack("<6I", 1, 0, loop_start, loop_end, 0, 0)

    new_chunks = []
    inserted = False
    for chunk_id, chunk_data in chunks:
        if chunk_id == b"data" and not inserted:
            new_chunks.append((b"smpl", smpl_body))
            inserted = True
        new_chunks.append((chunk_id, chunk_data))
    if not inserted:
        new_chunks.append((b"smpl", smpl_body))

    body = b""
    for chunk_id, chunk_data in new_chunks:
        body += chunk_id + struct.pack("<I", len(chunk_data)) + chunk_data
        if len(chunk_data) % 2:
            body += b"\x00"

    with open(wav_path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", len(body) + 4) + b"WAVE" + body)


# ---------------------------------------------------------------------------
# gnuplot helpers
# ---------------------------------------------------------------------------


def write_gnuplot_data(samples, path):
    """Write single-column sample data for gnuplot."""
    with open(path, "w") as f:
        for sample in samples:
            f.write(f"{float(sample)}\n")


def gnuplot_ascii_plot(samples, width=120, height=20):
    """Generate ASCII waveform plot using gnuplot dumb terminal."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as tmp:
        data_path = tmp.name
        write_gnuplot_data(samples, data_path)

    safe_path = data_path.replace("'", "'\\''")
    plot_cmd = (
        f"set terminal dumb {width} {height}; "
        f"unset xtics; unset ytics; "
        f"plot '{safe_path}' notitle with lines"
    )

    try:
        result = subprocess.run(
            ["gnuplot", "-e", plot_cmd],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.replace("\x0c", "").rstrip("\n")
    except FileNotFoundError:
        print("ERROR: gnuplot not found.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: gnuplot failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        Path(data_path).unlink(missing_ok=True)


def gnuplot_png_plot(samples, output_path, width=1920, height=960, line_color=None):
    """Render waveform plot as PNG using gnuplot."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dat", delete=False) as tmp:
        data_path = tmp.name
        write_gnuplot_data(samples, data_path)

    safe_data = data_path.replace("'", "'\\''")
    safe_output = str(output_path).replace("'", "'\\''")
    plot_cmd = (
        f"set term png size {width},{height}; "
        f"set output '{safe_output}'; "
        f"unset xtics; unset ytics; unset key; "
    )
    if line_color and line_color != "auto":
        safe_color = line_color.replace("'", "'\\''")
        plot_cmd += (
            f"set style line 1 linecolor rgb '{safe_color}'; "
            f"plot '{safe_data}' notitle with lines linestyle 1"
        )
    else:
        plot_cmd += f"plot '{safe_data}' notitle with lines"

    try:
        subprocess.run(
            ["gnuplot", "-e", plot_cmd],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        print("ERROR: gnuplot not found.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: gnuplot failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        Path(data_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Format converters
# ---------------------------------------------------------------------------


def samples_to_json_values(samples, decimal_places=6):
    """Convert float samples to rounded JSON-serializable values."""
    return [round(float(s), decimal_places) for s in samples]


def float_to_uint16(samples):
    """Convert float samples (-1..1) to unsigned 16-bit integers."""
    return np.clip((samples + 1.0) * 32767.5, 0, 65535).astype(np.uint16)


def format_uint16_c_array(values):
    """Format uint16 values as a C array literal (16 values per line)."""
    lines = []
    for i in range(0, len(values), 16):
        chunk = values[i : i + 16]
        lines.append(", ".join(f"{int(v):5d}" for v in chunk) + ",")
    return "\n".join(lines)


def bit_depth_subtype(bit_depth):
    """Map a target bit depth to a soundfile subtype."""
    if bit_depth == 32:
        return "FLOAT"
    elif bit_depth == 24:
        return "PCM_24"
    elif bit_depth == 8:
        return "PCM_U8"
    return "PCM_16"


def apply_dither_and_channels(samples, source_path, bit_depth, channels):
    """Apply TPDF dither for integer bit depths, then duplicate to stereo if requested."""
    if bit_depth in (8, 16, 24):
        quant_levels = 2 ** (bit_depth - 1)
        dither_amplitude = 1.0 / quant_levels
        rng = dither_rng_for_file(source_path)
        dither = rng.uniform(
            -dither_amplitude, dither_amplitude, len(samples)
        ) + rng.uniform(-dither_amplitude, dither_amplitude, len(samples))
        samples = np.clip(samples + dither, -1.0, 1.0)

    if channels == "stereo":
        samples = np.column_stack((samples, samples))

    return samples


def convert_wav(source_path, output_path, config):
    """Convert a single WAV file according to target config."""
    if sf is None:
        print("ERROR: soundfile required.", file=sys.stderr)
        sys.exit(1)

    samples = load_samples(source_path, config)

    audio_config = config.get("audio", {})
    bit_depth = audio_config.get("bit_depth", 16)
    sample_rate = audio_config.get("sample_rate", 44100)
    channels = audio_config.get("channels", "mono")

    subtype = bit_depth_subtype(bit_depth)
    samples = apply_dither_and_channels(samples, source_path, bit_depth, channels)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), samples, sample_rate, subtype=subtype)

    if config.get("metadata", {}).get("add_loop_points", False):
        add_smpl_loop_to_wav(output_path, loop_start=0, loop_end=len(samples) - 1)


def convert_raw(source_path, output_path, config):
    """Convert a single source file to headerless raw PCM according to target config."""
    if sf is None:
        print("ERROR: soundfile required.", file=sys.stderr)
        sys.exit(1)

    samples = load_samples(source_path, config)

    audio_config = config.get("audio", {})
    bit_depth = audio_config.get("bit_depth", 16)
    sample_rate = audio_config.get("sample_rate", 44100)
    channels = audio_config.get("channels", "mono")

    subtype = bit_depth_subtype(bit_depth)
    samples = apply_dither_and_channels(samples, source_path, bit_depth, channels)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), samples, sample_rate, subtype=subtype, format="RAW")


def convert_json_bank(bank_dir, output_base, config):
    """Convert all waveforms in a bank to a single JSON file.

    Filename/layout is hardcoded (flat `{bank}.json`) — unlike other formats,
    this does not consult naming/structure config.
    """
    waveforms = {}

    for wav_file in sorted(bank_dir.glob("*.wav")):
        samples = load_samples(wav_file, config)
        waveforms[wav_file.stem] = samples_to_json_values(samples)

    if not waveforms:
        return 0

    output_path = output_base / f"{bank_dir.name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write("{\n")
        items = list(waveforms.items())
        for i, (name, values) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            f.write(f'  "{name}": {json.dumps(values)}{comma}\n')
        f.write("}\n")

    return len(waveforms)


def convert_c_header(source_path, output_path, config):
    """Convert a WAV file to a Teensy-compatible C header."""
    metadata = config.get("metadata", {})
    base_name = source_path.stem

    samples = load_samples(source_path, config)
    values = float_to_uint16(samples)

    header = """/* Adventure Kid Waveforms (AKWF) converted for use with Teensy Audio Library
*
*  Adventure Kid Waveforms(AKWF) Open waveforms library
*  https://www.adventurekid.se/akrt/waveforms/adventure-kid-waveforms/
*
*  This code is in the public domain, CC0 1.0 Universal (CC0 1.0)
*  https://creativecommons.org/publicdomain/zero/1.0/
*
*  Converted by AKWF-FREE build system
*/
"""

    comment_block = f"/* {base_name} {len(values)} samples\n"
    if metadata.get("include_ascii_art", False):
        display = values.astype(np.float64) / 32767.5 - 1.0
        comment_block += gnuplot_ascii_plot(display) + "\n"
    comment_block += "*/\n\n"

    body = f"const uint16_t {base_name} [] = {{\n"
    body += format_uint16_c_array(values)
    body += "\n};\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(header + comment_block + body)


def convert_png(source_path, output_path, config):
    """Render a waveform plot as a PNG image using gnuplot."""
    samples = load_samples(source_path, config)
    metadata = config.get("metadata", {})
    width = metadata.get("image_width", 1920)
    height = metadata.get("image_height", 960)
    line_color = metadata.get("line_color")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gnuplot_png_plot(
        samples, output_path, width=width, height=height, line_color=line_color
    )


def write_json_manifest(output_base, bank_names, bank_filter=None):
    """Write manifest.json, merging with existing banks on partial builds."""
    manifest_path = output_base / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    if bank_filter and manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text())
            banks = sorted(set(existing.get("banks", [])) | set(bank_names))
        except (json.JSONDecodeError, OSError):
            banks = sorted(bank_names)
    else:
        banks = sorted(bank_names)

    manifest_path.write_text(json.dumps({"banks": banks}, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Build orchestration
# ---------------------------------------------------------------------------

DEFAULT_EXTENSIONS = {
    "wav": ".wav",
    "raw": ".raw",
    "c-header": ".h",
}


def output_path_for(wav_file, bank_dir, output_base, config, naming):
    """Compute output path for a source WAV file."""
    stem = wav_file.stem
    audio_format = config.get("audio", {}).get("format", "wav")
    ext = naming.get("extension") or DEFAULT_EXTENSIONS.get(audio_format, ".wav")

    fname_case = naming.get("filename_case", "preserve")
    if fname_case == "upper":
        stem = stem.upper()
    elif fname_case == "lower":
        stem = stem.lower()

    ext_case = naming.get("extension_case", "preserve")
    if ext_case == "upper":
        ext = ext.upper()
    elif ext_case == "lower":
        ext = ext.lower()

    output_filename = stem + ext

    if config.get("structure", {}).get("mirror_source", True):
        return output_base / bank_dir.name / output_filename
    return output_base / output_filename


def build_target(config, bank_filter=None, dry_run=False):
    """Build a complete target from config."""
    audio_format = config.get("audio", {}).get("format", "wav")
    output_base = DIST_DIR / config["output_dir"]
    skip_banks = config.get("skip", {}).get("banks", [])
    naming = config.get("naming", {})

    banks = get_source_banks(skip_banks)
    if bank_filter:
        banks = [b for b in banks if b.name == bank_filter]

    if not banks:
        print("No matching banks found.", file=sys.stderr)
        return 1

    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}Building target: {config['name']}")
    print(f"{prefix}Output: {output_base}")
    print(f"{prefix}Banks: {len(banks)}")

    total_files = 0
    bank_names = []
    errors = 0

    for bank_dir in tqdm(banks, desc="Banks", disable=dry_run):
        wav_files = sorted(bank_dir.glob("*.wav"))
        if not wav_files:
            continue

        if audio_format == "json":
            if dry_run:
                count = len(wav_files)
                print(
                    f"  would write: {output_base / (bank_dir.name + '.json')} ({count} waveforms)"
                )
            else:
                try:
                    count = convert_json_bank(bank_dir, output_base, config)
                except Exception as e:
                    print(f"  ERROR {bank_dir.name}: {e}", file=sys.stderr)
                    errors += 1
                    continue
            if count:
                total_files += count
                bank_names.append(bank_dir.name)
            continue

        for wav_file in wav_files:
            output_path = output_path_for(
                wav_file, bank_dir, output_base, config, naming
            )

            if dry_run:
                if total_files < 5:
                    print(f"  would write: {output_path}")
                total_files += 1
                continue

            try:
                if audio_format == "wav":
                    convert_wav(wav_file, output_path, config)
                elif audio_format == "raw":
                    convert_raw(wav_file, output_path, config)
                elif audio_format == "png":
                    convert_png(wav_file, output_path, config)
                elif audio_format == "c-header":
                    convert_c_header(wav_file, output_path, config)
                else:
                    print(f"ERROR: Unsupported format: {audio_format}", file=sys.stderr)
                    return errors + 1
            except Exception as e:
                print(f"  ERROR {wav_file.name}: {e}", file=sys.stderr)
                errors += 1
                continue

            total_files += 1

    if dry_run and total_files >= 5:
        print(f"  ... and {total_files - 5} more files")

    if audio_format == "json" and config.get("metadata", {}).get("generate_manifest"):
        if dry_run:
            print(
                f"  would write: {output_base / 'manifest.json'} ({len(bank_names)} banks)"
            )
        else:
            write_json_manifest(output_base, bank_names, bank_filter=bank_filter)

    verb = "Would convert" if dry_run else "Converted"
    print(f"{prefix}Done. {verb} {total_files} files.", end="")
    if errors:
        print(f" ({errors} errors)", end="")
    print()

    return errors


def list_targets():
    """List all available target definitions."""
    targets = sorted(TARGETS_DIR.glob("*.yml"))
    if not targets:
        print("No target definitions found in targets/")
        return

    total = 0
    for t in targets:
        try:
            with open(t) as f:
                raw = yaml.safe_load(f)

            if raw.get("type") == "matrix":
                configs = expand_matrix(raw)
                desc = raw.get("description", "").strip().split("\n")[0][:60]
                print(f"  {t.name:<30} [MATRIX: {len(configs)} targets]")
                if desc:
                    print(f"  {'':30} {desc}")
                print()
                for c in configs:
                    print(f"    → {c['output_dir']}")
                    total += 1
                print()
            else:
                name = raw.get("name", t.stem)
                desc = raw.get("description", "").strip().split("\n")[0][:60]
                print(f"  {t.name:<30} {name}")
                if desc:
                    print(f"  {'':30} {desc}")
                print()
                total += 1
        except Exception as e:
            print(f"  {t.name:<30} (error: {e})")

    print(f"Total: {total} build targets")


def main():
    parser = argparse.ArgumentParser(description="AKWF-FREE Conversion Engine")
    parser.add_argument("--target", type=str, help="Path to target YAML definition")
    parser.add_argument("--all", action="store_true", help="Build all targets")
    parser.add_argument("--list", action="store_true", help="List available targets")
    parser.add_argument(
        "--bank", type=str, help="Process only this bank (e.g., AKWF_0001)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done"
    )

    args = parser.parse_args()

    if args.list:
        list_targets()
        return

    total_errors = 0

    if args.all:
        targets = sorted(TARGETS_DIR.glob("*.yml"))
        for t in targets:
            configs = load_target(t)
            for config in configs:
                total_errors += build_target(
                    config, bank_filter=args.bank, dry_run=args.dry_run
                )
        if total_errors:
            sys.exit(1)
        return

    if args.target:
        target_path = Path(args.target)
        if not target_path.exists():
            print(f"ERROR: Target file not found: {target_path}", file=sys.stderr)
            sys.exit(1)
        configs = load_target(target_path)
        for config in configs:
            total_errors += build_target(
                config, bank_filter=args.bank, dry_run=args.dry_run
            )
        if total_errors:
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

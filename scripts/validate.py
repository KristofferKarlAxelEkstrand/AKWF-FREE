#!/usr/bin/env python3
"""
Validate converted waveform output.

Checks:
- File format correctness (bit depth, sample rate, channels)
- Sample count matches target
- Peak levels within expected range
- Loop continuity (first/last sample proximity)
- No silence or corruption

Usage:
    python3 scripts/validate.py dist/AKWF--1024smp-16bit-44_1k/
    python3 scripts/validate.py dist/AKWF--1024smp-16bit-44_1k/ --target targets/akwf-standard.yml
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# soundfile subtype names for expected bit depths
EXPECTED_SUBTYPES = {
    8: frozenset({"PCM_U8"}),
    16: frozenset({"PCM_16"}),
    24: frozenset({"PCM_24"}),
    32: frozenset({"FLOAT", "PCM_32"}),
}


def read_smpl_loop(filepath):
    """Read loop start/end from WAV smpl chunk. Returns (start, end) or None."""
    with open(filepath, "rb") as f:
        data = f.read()

    idx = data.find(b"smpl")
    if idx < 0:
        return None

    size = struct.unpack("<I", data[idx + 4 : idx + 8])[0]
    body = data[idx + 8 : idx + 8 + size]
    if len(body) < 44:
        return None

    loop_start, loop_end = struct.unpack("<II", body[44:52])
    return loop_start, loop_end


def _validate_sample_content(samples):
    """Peak/silence/clipping/loop-continuity/DC-offset checks shared by wav and raw."""
    issues = []

    # Check for silence
    peak = np.max(np.abs(samples))
    if peak < 0.001:
        issues.append(f"File appears silent (peak={peak:.6f})")

    # Check for clipping (above 0 dBFS)
    if peak > 1.0:
        issues.append(f"File clips (peak={peak:.6f} > 1.0)")

    # Check loop continuity
    # For a seamlessly loopable single-cycle waveform, the difference
    # between last sample and first sample should be small relative to
    # the maximum delta in the waveform
    if len(samples) > 1:
        loop_gap = abs(samples[-1] - samples[0])
        max_delta = np.max(np.abs(np.diff(samples)))
        if max_delta > 0 and loop_gap > max_delta * 2:
            issues.append(
                f"Loop discontinuity: gap={loop_gap:.6f}, max_delta={max_delta:.6f}"
            )

    # Check DC offset
    dc = np.mean(samples)
    if abs(dc) > 0.01:
        issues.append(f"Significant DC offset: {dc:.6f}")

    return issues


def validate_wav(
    filepath,
    expected_length=None,
    expected_sr=None,
    expected_bits=None,
    expect_loop_points=False,
    channels="mono",
):
    """Validate a single WAV file. Returns list of issues."""
    issues = []

    try:
        info = sf.info(str(filepath))
    except Exception as e:
        return [f"Cannot read file: {e}"]

    # Check channels
    expected_channels = 2 if channels == "stereo" else 1
    if info.channels != expected_channels:
        issues.append(f"Expected {expected_channels} channel(s), got {info.channels}")

    # Check sample rate
    if expected_sr and info.samplerate != expected_sr:
        issues.append(f"Expected {expected_sr}Hz, got {info.samplerate}Hz")

    # Check length
    if expected_length and info.frames != expected_length:
        issues.append(f"Expected {expected_length} samples, got {info.frames}")

    # Check bit depth
    if expected_bits:
        expected_subtypes = EXPECTED_SUBTYPES.get(expected_bits)
        if expected_subtypes and info.subtype not in expected_subtypes:
            issues.append(f"Expected {expected_bits}-bit, got {info.subtype}")

    # Read samples for content validation
    samples, sr = sf.read(str(filepath), dtype="float64")
    if len(samples.shape) > 1:
        samples = samples[:, 0]

    issues.extend(_validate_sample_content(samples))

    # Check WAV smpl loop chunk
    if expect_loop_points:
        loop = read_smpl_loop(filepath)
        if loop is None:
            issues.append("Expected smpl loop chunk, not found")
        else:
            loop_start, loop_end = loop
            expected_end = (expected_length - 1) if expected_length else loop_end
            if loop_start != 0:
                issues.append(f"Loop start expected 0, got {loop_start}")
            if expected_length and loop_end != expected_end:
                issues.append(f"Loop end expected {expected_end}, got {loop_end}")

    return issues


def _raw_subtype_for_bit_depth(bit_depth):
    """Map a bit depth to the soundfile subtype needed to decode headerless raw PCM."""
    if bit_depth == 32:
        return "FLOAT"
    elif bit_depth == 24:
        return "PCM_24"
    elif bit_depth == 8:
        return "PCM_U8"
    return "PCM_16"


def validate_raw(
    filepath,
    expected_length=None,
    expected_sr=None,
    expected_bits=None,
    channels="mono",
):
    """Validate a single headerless raw PCM file. Returns list of issues."""
    subtype = _raw_subtype_for_bit_depth(expected_bits or 16)
    num_channels = 2 if channels == "stereo" else 1

    try:
        samples, sr = sf.read(
            str(filepath),
            format="RAW",
            samplerate=expected_sr or 44100,
            channels=num_channels,
            subtype=subtype,
            dtype="float64",
        )
    except Exception as e:
        return [f"Cannot read raw file: {e}"]

    issues = []

    if len(samples.shape) > 1:
        frames = samples.shape[0]
        samples = samples[:, 0]
    else:
        frames = len(samples)

    if expected_length and frames != expected_length:
        issues.append(f"Expected {expected_length} samples, got {frames}")

    issues.extend(_validate_sample_content(samples))

    return issues


def validate_json(filepath, expected_length=None):
    """Validate a bank JSON file. Returns list of issues."""
    issues = []

    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except OSError as e:
        return [f"Cannot read file: {e}"]

    if not isinstance(data, dict):
        return ["Expected top-level object"]

    if not data:
        return ["Empty bank (no waveforms)"]

    for name, samples in data.items():
        if not isinstance(samples, list):
            issues.append(f"{name}: expected array, got {type(samples).__name__}")
            continue
        if expected_length and len(samples) != expected_length:
            issues.append(
                f"{name}: expected {expected_length} samples, got {len(samples)}"
            )
        if not samples:
            issues.append(f"{name}: empty sample array")
            continue

        non_numeric = [v for v in samples if not isinstance(v, (int, float))]
        if non_numeric:
            issues.append(f"{name}: non-numeric samples")
            continue

        peak = max(abs(float(v)) for v in samples)
        if peak < 0.001:
            issues.append(f"{name}: appears silent (peak={peak:.6f})")
        if peak > 1.001:
            issues.append(f"{name}: exceeds -1..1 range (peak={peak:.6f})")

    return issues


def validate_json_manifest(manifest_path, expected_banks=None):
    """Validate manifest.json lists expected banks."""
    issues = []

    try:
        with open(manifest_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except OSError as e:
        return [f"Cannot read file: {e}"]

    banks = data.get("banks")
    if not isinstance(banks, list) or not banks:
        issues.append("Expected non-empty 'banks' array")
        return issues

    if expected_banks:
        missing = sorted(set(expected_banks) - set(banks))
        if missing:
            issues.append(f"Missing banks in manifest: {', '.join(missing)}")

    return issues


def parse_c_header_samples(text):
    """Extract uint16 sample values from a Teensy C header."""
    match = re.search(r"const uint16_t\s+\w+\s*\[\]\s*=\s*\{", text)
    if not match:
        return None

    start = text.find("{", match.start())
    end = text.find("};", start)
    if start < 0 or end < 0:
        return None

    values = []
    for part in text[start + 1 : end].split(","):
        part = part.strip()
        if part.isdigit():
            values.append(int(part))
    return values


def validate_c_header(filepath, expected_length=None):
    """Validate a Teensy C header file. Returns list of issues."""
    issues = []

    try:
        text = filepath.read_text()
    except OSError as e:
        return [f"Cannot read file: {e}"]

    name = filepath.stem
    if not re.search(rf"const uint16_t\s+{re.escape(name)}\s*\[\]", text):
        issues.append(f"Missing const uint16_t {name} [] declaration")

    values = parse_c_header_samples(text)
    if values is None:
        return issues + ["No sample array found"]
    if not values:
        return issues + ["Empty sample array"]

    if expected_length and len(values) != expected_length:
        issues.append(f"Expected {expected_length} samples, got {len(values)}")

    vmin, vmax = min(values), max(values)
    if vmin < 0 or vmax > 65535:
        issues.append(f"Values out of uint16 range: min={vmin}, max={vmax}")
    if vmax - vmin < 10:
        issues.append(f"Appears silent or flat (range={vmax - vmin})")

    return issues


def read_png_dimensions(data):
    """Read width/height from PNG IHDR chunk."""
    if len(data) < 24 or data[:8] != PNG_SIGNATURE:
        return None
    return struct.unpack(">II", data[16:24])


def validate_png(filepath, expected_width=None, expected_height=None):
    """Validate a waveform PNG plot. Returns list of issues."""
    issues = []

    try:
        data = filepath.read_bytes()
    except OSError as e:
        return [f"Cannot read file: {e}"]

    dims = read_png_dimensions(data)
    if dims is None:
        return ["Invalid PNG signature or truncated IHDR chunk"]

    width, height = dims
    if len(data) < 100:
        issues.append(f"File too small ({len(data)} bytes)")

    if expected_width and width != expected_width:
        issues.append(f"Expected width {expected_width}, got {width}")
    if expected_height and height != expected_height:
        issues.append(f"Expected height {expected_height}, got {height}")

    return issues


def _run_validation(files, check_dir, validate_fn, verbose):
    """Run validate_fn over files, printing FAIL/OK per file. Returns error count."""
    error_count = 0
    for f in files:
        issues = validate_fn(f)
        rel_path = f.relative_to(check_dir)
        if issues:
            print(f"  FAIL {rel_path}")
            for issue in issues:
                print(f"       - {issue}")
            error_count += 1
        elif verbose:
            print(f"  OK   {rel_path}")
    return error_count


def detect_audio_format(check_dir):
    """Guess the output format present in check_dir when no --target is given."""
    if sorted(check_dir.rglob("*.wav")) + sorted(check_dir.rglob("*.WAV")):
        return "wav"
    if sorted(check_dir.glob("*.json")):
        return "json"
    if sorted(check_dir.rglob("*.h")):
        return "c-header"
    if sorted(check_dir.rglob("*.png")):
        return "png"
    if sorted(check_dir.rglob("*.raw")):
        return "raw"
    return "wav"


def main():
    parser = argparse.ArgumentParser(description="Validate AKWF converted output")
    parser.add_argument("directory", type=str, help="Directory to validate")
    parser.add_argument("--target", type=str, help="Target YAML for expected specs")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show all files, not just errors"
    )

    args = parser.parse_args()

    check_dir = Path(args.directory)
    if not check_dir.exists():
        print(f"ERROR: Directory not found: {check_dir}", file=sys.stderr)
        sys.exit(1)

    # Load expected specs from target
    audio_format = None
    expected_length = None
    expected_sr = None
    expected_bits = None
    expected_width = None
    expected_height = None
    generate_manifest = False
    channels = "mono"
    raw_extension = "*.raw"

    if args.target:
        try:
            with open(args.target) as f:
                config = yaml.safe_load(f)
            # Handle matrix targets — use defaults
            if config.get("type") == "matrix":
                config = config.get("defaults", {})
            audio = config.get("audio", {})
            audio_format = audio.get("format", "wav")
            expected_length = audio.get("length_samples")
            expected_sr = audio.get("sample_rate")
            expected_bits = audio.get("bit_depth")
            channels = audio.get("channels", "mono")
            metadata = config.get("metadata", {})
            expected_width = metadata.get("image_width")
            expected_height = metadata.get("image_height")
            generate_manifest = metadata.get("generate_manifest", False)
            naming_ext = config.get("naming", {}).get("extension")
            if naming_ext:
                raw_extension = f"*{naming_ext}"
        except Exception as e:
            print(f"Warning: Could not load target: {e}")

    if audio_format is None:
        audio_format = detect_audio_format(check_dir)

    print(f"Validating {audio_format} output in {check_dir}")
    if expected_length:
        print(
            f"Expected: {expected_length} samples, {expected_sr}Hz, {expected_bits}-bit"
        )
    print()

    if audio_format == "wav":
        files = sorted(check_dir.rglob("*.wav")) + sorted(check_dir.rglob("*.WAV"))
        if not files:
            print(f"No WAV files found in {check_dir}")
            sys.exit(1)
        error_count = _run_validation(
            files,
            check_dir,
            lambda f: validate_wav(
                f, expected_length, expected_sr, expected_bits, channels=channels
            ),
            args.verbose,
        )
        total = len(files)

    elif audio_format == "raw":
        files = sorted(check_dir.rglob(raw_extension))
        if not files:
            print(f"No raw PCM files found in {check_dir} (looked for {raw_extension})")
            sys.exit(1)
        error_count = _run_validation(
            files,
            check_dir,
            lambda f: validate_raw(
                f, expected_length, expected_sr, expected_bits, channels=channels
            ),
            args.verbose,
        )
        total = len(files)

    elif audio_format == "json":
        files = sorted(f for f in check_dir.glob("*.json") if f.name != "manifest.json")
        if not files:
            print(f"No JSON bank files found in {check_dir}")
            sys.exit(1)
        error_count = _run_validation(
            files,
            check_dir,
            lambda f: validate_json(f, expected_length),
            args.verbose,
        )
        total = len(files)

        manifest_path = check_dir / "manifest.json"
        if generate_manifest or manifest_path.exists():
            total += 1
            if not manifest_path.exists():
                issues = ["manifest.json missing"]
            else:
                issues = validate_json_manifest(manifest_path, [f.stem for f in files])
            if issues:
                print("  FAIL manifest.json")
                for issue in issues:
                    print(f"       - {issue}")
                error_count += 1
            elif args.verbose:
                print("  OK   manifest.json")

    elif audio_format == "c-header":
        files = sorted(check_dir.rglob("*.h"))
        if not files:
            print(f"No C header files found in {check_dir}")
            sys.exit(1)
        error_count = _run_validation(
            files,
            check_dir,
            lambda f: validate_c_header(f, expected_length),
            args.verbose,
        )
        total = len(files)

    elif audio_format == "png":
        files = sorted(check_dir.rglob("*.png"))
        if not files:
            print(f"No PNG files found in {check_dir}")
            sys.exit(1)
        error_count = _run_validation(
            files,
            check_dir,
            lambda f: validate_png(f, expected_width, expected_height),
            args.verbose,
        )
        total = len(files)

    else:
        print(f"ERROR: Unsupported format: {audio_format}", file=sys.stderr)
        sys.exit(1)

    print()
    passed = total - error_count
    print(f"Results: {passed}/{total} passed, {error_count} errors")

    sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()

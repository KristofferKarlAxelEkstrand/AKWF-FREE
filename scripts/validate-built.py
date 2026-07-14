#!/usr/bin/env python3
"""
Validate built outputs in dist/ against target definitions.

Usage:
    python3 scripts/validate-built.py
    python3 scripts/validate-built.py --bank AKWF_0001
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
TARGETS_DIR = ROOT / "targets"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from targets import load_target  # noqa: E402
from validate import (  # noqa: E402
    validate_c_header,
    validate_json,
    validate_json_manifest,
    validate_png,
    validate_raw,
    validate_wav,
)


def _bank_matches(path, bank_filter, flat=False):
    """Return True if path belongs to the filtered bank."""
    if not bank_filter:
        return True
    if flat:
        return path.stem == bank_filter
    return path.parent.name == bank_filter


def validate_wav_output(config, output_dir, bank_filter=None):
    """Validate WAV files for one target config."""
    audio = config.get("audio", {})
    expected_length = audio.get("length_samples")
    expected_sr = audio.get("sample_rate")
    expected_bits = audio.get("bit_depth")
    channels = audio.get("channels", "mono")
    expect_loop = config.get("metadata", {}).get("add_loop_points", False)

    wav_files = sorted(output_dir.rglob("*.wav")) + sorted(output_dir.rglob("*.WAV"))
    wav_files = [f for f in wav_files if _bank_matches(f, bank_filter)]

    if not wav_files:
        print(f"  FAIL {config['output_dir']} (no WAV files)")
        return 0, 1

    passed = failed = 0
    for wav_file in wav_files:
        issues = validate_wav(
            wav_file,
            expected_length,
            expected_sr,
            expected_bits,
            expect_loop_points=expect_loop,
            channels=channels,
        )
        rel = wav_file.relative_to(output_dir)
        if issues:
            print(f"  FAIL {config['output_dir']}/{rel}")
            for issue in issues:
                print(f"       - {issue}")
            failed += 1
        else:
            passed += 1

    print(f"  OK   {config['output_dir']}: {passed}/{passed + failed} passed")
    return passed, failed


def validate_raw_output(config, output_dir, bank_filter=None):
    """Validate headerless raw PCM files for one target config."""
    audio = config.get("audio", {})
    expected_length = audio.get("length_samples")
    expected_sr = audio.get("sample_rate")
    expected_bits = audio.get("bit_depth")
    channels = audio.get("channels", "mono")
    ext = config.get("naming", {}).get("extension", ".raw")

    raw_files = sorted(output_dir.rglob(f"*{ext}"))
    raw_files = [f for f in raw_files if _bank_matches(f, bank_filter)]

    if not raw_files:
        print(f"  FAIL {config['output_dir']} (no raw PCM files)")
        return 0, 1

    passed = failed = 0
    for raw_file in raw_files:
        issues = validate_raw(
            raw_file,
            expected_length,
            expected_sr,
            expected_bits,
            channels=channels,
        )
        rel = raw_file.relative_to(output_dir)
        if issues:
            print(f"  FAIL {config['output_dir']}/{rel}")
            for issue in issues:
                print(f"       - {issue}")
            failed += 1
        else:
            passed += 1

    print(f"  OK   {config['output_dir']}: {passed}/{passed + failed} passed")
    return passed, failed


def validate_json_output(config, output_dir, bank_filter=None):
    """Validate JSON bank files and optional manifest."""
    audio = config.get("audio", {})
    expected_length = audio.get("length_samples")
    metadata = config.get("metadata", {})

    json_files = sorted(output_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "manifest.json"]
    json_files = [f for f in json_files if _bank_matches(f, bank_filter, flat=True)]

    if not json_files:
        print(f"  FAIL {config['output_dir']} (no JSON bank files)")
        return 0, 1

    passed = failed = 0
    for json_file in json_files:
        issues = validate_json(json_file, expected_length)
        rel = json_file.relative_to(output_dir)
        if issues:
            print(f"  FAIL {config['output_dir']}/{rel}")
            for issue in issues:
                print(f"       - {issue}")
            failed += 1
        else:
            passed += 1

    if metadata.get("generate_manifest"):
        manifest_path = output_dir / "manifest.json"
        if not manifest_path.exists():
            print(f"  FAIL {config['output_dir']}/manifest.json (missing)")
            failed += 1
        else:
            expected_banks = [f.stem for f in json_files] if bank_filter else None
            issues = validate_json_manifest(manifest_path, expected_banks)
            if issues:
                print(f"  FAIL {config['output_dir']}/manifest.json")
                for issue in issues:
                    print(f"       - {issue}")
                failed += 1
            else:
                passed += 1

    print(f"  OK   {config['output_dir']}: {passed}/{passed + failed} passed")
    return passed, failed


def validate_c_header_output(config, output_dir, bank_filter=None):
    """Validate C header files for one target config."""
    audio = config.get("audio", {})
    expected_length = audio.get("length_samples")

    header_files = sorted(output_dir.rglob("*.h"))
    header_files = [f for f in header_files if _bank_matches(f, bank_filter)]

    if not header_files:
        print(f"  FAIL {config['output_dir']} (no C header files)")
        return 0, 1

    passed = failed = 0
    for header_file in header_files:
        issues = validate_c_header(header_file, expected_length)
        rel = header_file.relative_to(output_dir)
        if issues:
            print(f"  FAIL {config['output_dir']}/{rel}")
            for issue in issues:
                print(f"       - {issue}")
            failed += 1
        else:
            passed += 1

    print(f"  OK   {config['output_dir']}: {passed}/{passed + failed} passed")
    return passed, failed


def validate_png_output(config, output_dir, bank_filter=None):
    """Validate PNG plot files for one target config."""
    metadata = config.get("metadata", {})
    expected_width = metadata.get("image_width")
    expected_height = metadata.get("image_height")

    png_files = sorted(output_dir.rglob("*.png"))
    png_files = [f for f in png_files if _bank_matches(f, bank_filter)]

    if not png_files:
        print(f"  FAIL {config['output_dir']} (no PNG files)")
        return 0, 1

    passed = failed = 0
    for png_file in png_files:
        issues = validate_png(png_file, expected_width, expected_height)
        rel = png_file.relative_to(output_dir)
        if issues:
            print(f"  FAIL {config['output_dir']}/{rel}")
            for issue in issues:
                print(f"       - {issue}")
            failed += 1
        else:
            passed += 1

    print(f"  OK   {config['output_dir']}: {passed}/{passed + failed} passed")
    return passed, failed


def validate_config_output(config, bank_filter=None):
    """Validate built output for one target config. Returns (passed, failed)."""
    audio = config.get("audio", {})
    audio_format = audio.get("format", "wav")
    output_dir = DIST_DIR / config["output_dir"]

    if not output_dir.exists():
        print(f"  FAIL {config['output_dir']} (output not built)")
        return 0, 1

    validators = {
        "wav": validate_wav_output,
        "raw": validate_raw_output,
        "json": validate_json_output,
        "c-header": validate_c_header_output,
        "png": validate_png_output,
    }

    validator = validators.get(audio_format)
    if validator is None:
        print(f"  SKIP {config['output_dir']} (unsupported format: {audio_format})")
        return 0, 0

    return validator(config, output_dir, bank_filter=bank_filter)


def main():
    parser = argparse.ArgumentParser(description="Validate built AKWF targets in dist/")
    parser.add_argument(
        "--bank", type=str, help="Validate only this bank (e.g., AKWF_0001)"
    )
    args = parser.parse_args()

    total_passed = 0
    total_failed = 0

    print(f"Validating dist/ outputs{f' (bank: {args.bank})' if args.bank else ''}")
    print()

    for yml in sorted(TARGETS_DIR.glob("*.yml")):
        configs = load_target(yml)
        for config in configs:
            passed, failed = validate_config_output(config, bank_filter=args.bank)
            total_passed += passed
            total_failed += failed

    print()
    print(f"Results: {total_passed} passed, {total_failed} failed")
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()

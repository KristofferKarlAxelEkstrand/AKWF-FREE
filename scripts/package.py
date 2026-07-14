#!/usr/bin/env python3
"""
Package built targets into zip archives for GitHub releases.

Usage:
    python3 scripts/package.py --target targets/akwf-standard.yml
    python3 scripts/package.py --all
"""

import argparse
import sys
import zipfile
from pathlib import Path

from targets import load_target

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
RELEASES_DIR = ROOT / "releases"
TARGETS_DIR = ROOT / "targets"


def package_target(config):
    """Create a zip archive for a built target."""
    output_dir_name = config["output_dir"]
    source_dir = DIST_DIR / output_dir_name

    if not source_dir.exists():
        print(f"  SKIP {output_dir_name} (not built yet)")
        return False

    packaging = config.get("packaging", {})
    if not packaging.get("zip", True):
        print(f"  SKIP {output_dir_name} (zip disabled)")
        return False

    zip_name = packaging.get("zip_name", "auto")
    if zip_name == "auto":
        zip_name = f"{output_dir_name}.zip"

    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RELEASES_DIR / zip_name

    # Collect files
    all_files = sorted(source_dir.rglob("*"))
    files_to_zip = [f for f in all_files if f.is_file()]

    if not files_to_zip:
        print(f"  SKIP {output_dir_name} (no files)")
        return False

    print(f"  Packaging {output_dir_name} → {zip_name} ({len(files_to_zip)} files)")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath in files_to_zip:
            arcname = filepath.relative_to(DIST_DIR)
            zf.write(filepath, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"    Created: {zip_path.name} ({size_mb:.1f} MB)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Package AKWF targets into zip archives"
    )
    parser.add_argument("--target", type=str, help="Target YAML to package")
    parser.add_argument("--all", action="store_true", help="Package all built targets")

    args = parser.parse_args()

    if args.all:
        targets = sorted(TARGETS_DIR.glob("*.yml"))
        print(f"Packaging {len(targets)} targets...\n")
        count = 0
        for t in targets:
            configs = load_target(t)
            for config in configs:
                if package_target(config):
                    count += 1
        print(f"\nDone. Created {count} archives in releases/")
        return

    if args.target:
        target_path = Path(args.target)
        if not target_path.exists():
            print(f"ERROR: Target file not found: {target_path}", file=sys.stderr)
            sys.exit(1)
        configs = load_target(target_path)
        for config in configs:
            package_target(config)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

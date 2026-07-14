"""Load and expand AKWF target YAML definitions."""

import copy
import itertools
import sys
from pathlib import Path

import yaml


def load_target(target_path):
    """Load and validate a target YAML definition.

    Returns a list of configs (matrix targets expand to multiple).
    """
    with open(target_path, "r") as f:
        config = yaml.safe_load(f)

    if config.get("type") == "matrix":
        return expand_matrix(config)

    required = ["name", "output_dir", "audio"]
    for field in required:
        if field not in config:
            print(f"ERROR: Target missing required field: {field}", file=sys.stderr)
            sys.exit(1)

    return [config]


def expand_matrix(matrix_config):
    """Expand a matrix target definition into individual configs."""
    matrix = matrix_config["matrix"]
    defaults = matrix_config.get("defaults", {})
    template = matrix_config.get("output_template", {})

    lengths = matrix["length_samples"]
    bit_depths = matrix["bit_depth"]
    sample_rates = matrix["sample_rate"]

    configs = []
    for length, bits, rate in itertools.product(lengths, bit_depths, sample_rates):
        rate_k = str(rate // 1000)
        if rate % 1000:
            rate_k = f"{rate // 1000}_{(rate % 1000) // 100}"  # e.g., "44_1"

        config = copy.deepcopy(defaults)

        config.setdefault("audio", {})
        config["audio"]["length_samples"] = length
        config["audio"]["bit_depth"] = bits
        config["audio"]["sample_rate"] = rate

        dir_template = template.get("dir", "AKWF-{length}smp-{bits}bit-{rate_k}k")
        name_template = template.get("name", "AKWF {length}smp {bits}-bit {rate_k}kHz")
        zip_template = template.get("zip", "{dir}.zip")

        fmt = {"length": length, "bits": bits, "rate_k": rate_k}
        config["output_dir"] = dir_template.format(**fmt)
        config["name"] = name_template.format(**fmt)

        config.setdefault("packaging", {})
        config["packaging"]["zip"] = True
        config["packaging"]["zip_name"] = zip_template.format(
            dir=config["output_dir"], **fmt
        )

        configs.append(config)

    return configs

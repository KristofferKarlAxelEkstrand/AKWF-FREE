# AKWF-FREE — build, check, validate, package
#
# Usage:
#   make check              # format + list targets
#   make smoke              # CI-style: one bank per target YAML
#   make build              # full library build (slow)
#   make build BANK=AKWF_0001 TARGET=targets/akai-mpc.yml
#   make validate             # validate built outputs
#   make package            # zip dist/ targets to releases/
#   make clean              # remove dist/ and releases/

.PHONY: check smoke build dry-run validate package clean list help

PYTHON ?= python3
BANK ?=
TARGET ?=

help:
	@echo "AKWF-FREE Makefile targets:"
	@echo "  make check     - format checks and list build targets"
	@echo "  make smoke     - build one bank per target YAML (CI default)"
	@echo "  make dry-run   - preview build without writing files"
	@echo "  make build     - build targets (all, or TARGET=..., BANK=...)"
	@echo "  make validate  - validate built outputs in dist/"
	@echo "  make package   - create zip archives in releases/"
	@echo "  make clean     - remove dist/ and releases/"
	@echo "  make list      - list available target definitions"

check:
	bash scripts/check-format.sh
	$(PYTHON) scripts/convert.py --list

smoke:
	bash scripts/ci-smoke.sh

build:
ifdef TARGET
	$(PYTHON) scripts/convert.py --target $(TARGET) $(if $(BANK),--bank $(BANK),)
else ifdef BANK
	$(PYTHON) scripts/convert.py --all --bank $(BANK)
else
	$(PYTHON) scripts/convert.py --all
endif

dry-run:
ifdef TARGET
	$(PYTHON) scripts/convert.py --target $(TARGET) $(if $(BANK),--bank $(BANK),) --dry-run
else
	$(PYTHON) scripts/convert.py --all $(if $(BANK),--bank $(BANK),) --dry-run
endif

validate:
	$(PYTHON) scripts/validate-built.py $(if $(BANK),--bank $(BANK),)

package:
	$(PYTHON) scripts/package.py --all

clean:
	rm -rf dist releases

list:
	$(PYTHON) scripts/convert.py --list

format:
	pre-commit run --all-files

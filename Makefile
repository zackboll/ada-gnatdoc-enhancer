PYTHON ?= python3
.PHONY: help test conformance compile wheel browser
help:
	@printf '%s\n' \
	  'make test         Offline Python unit and mutation tests' \
	  'make conformance  Four synthetic GNATdoc profiles, deterministic builds' \
	  'make compile      Python bytecode/syntax compilation' \
	  'make wheel        Build standalone Python wheel (requires build backend)' \
	  'make browser      Optional Playwright/Chromium browser checks'
test:
	@PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
conformance:
	@PYTHONPATH=src $(PYTHON) -m ada_gnatdoc_enhancer conformance --fixtures tests/fixtures
compile:
	@$(PYTHON) -m compileall -q src
wheel:
	@$(PYTHON) -m pip wheel --no-build-isolation --no-deps --wheel-dir dist .
browser:
	@PYTHONPATH=src $(PYTHON) scripts/test_browser.py

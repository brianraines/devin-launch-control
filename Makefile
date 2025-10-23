.PHONY: install format lint test check

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -e .[dev]

format:
	$(PYTHON) -m black launch_control tests

lint:
	$(PYTHON) -m ruff check launch_control tests

test:
	$(PYTHON) -m pytest

check: format lint test
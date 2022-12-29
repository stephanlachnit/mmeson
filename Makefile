# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

PYTHON ?= python3

.PHONY: default
default: egg_info

## build tagerts

.PHONY: egg_info
egg_info:
	@$(PYTHON) setup.py egg_info

.PHONY: docs
docs: egg_info
	make -C docs html

.PHONY: build
build:
	@$(PYTHON) -m build

## lint targets

.PHONY: lint
lint: flake8 pylint reuse

.PHONY: flake8
flake8:
	@$(PYTHON) -m flake8 src/mmeson tests setup.py docs/source/conf.py

.PHONY: pylint
pylint:
	@$(PYTHON) -m pylint src/mmeson tests setup.py docs/source/conf.py

.PHONY: reuse
reuse:
	@$(PYTHON) -m reuse lint

## test targets

.PHONY: test
test: pytest

.PHONY: pytest
pytest: egg_info
	@$(PYTHON) -m pytest

## misc tagets

.PHONY: clean
clean:
	@$(PYTHON) -Bc "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	@$(PYTHON) -Bc "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*.egg-info')]"
	@$(PYTHON) -Bc "import shutil; shutil.rmtree('.pytest_cache', ignore_errors=True)"
	@$(PYTHON) -Bc "import shutil; shutil.rmtree('build', ignore_errors=True)"
	@$(PYTHON) -Bc "import shutil; shutil.rmtree('dist', ignore_errors=True)"
	make -C docs clean

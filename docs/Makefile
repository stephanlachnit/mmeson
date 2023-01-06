# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

PYTHON ?= python3

export PYTHONPATH=../src/

.PHONY: help
help:
	@$(PYTHON) -m sphinx -M help source build

.PHONY: clean
clean:
	@$(PYTHON) -Bc "import shutil; shutil.rmtree('build', ignore_errors=True)"
	@$(PYTHON) -Bc "import shutil, os.path; shutil.rmtree(os.path.join('source', 'api'), ignore_errors=True)"
	@$(PYTHON) -Bc "import pathlib; pathlib.Path('source', 'README.md').unlink(missing_ok=True)"
	@$(PYTHON) -Bc "import shutil, os.path; shutil.rmtree(os.path.join('source', 'screenshots'), ignore_errors=True)"

.PHONY: Makefile
%: Makefile
	@$(PYTHON) -m sphinx -M $@ source build $(O)

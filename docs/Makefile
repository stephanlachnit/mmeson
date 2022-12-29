# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

export PYTHONPATH=../src/

.PHONY: help
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: clean
clean:
	python3 -Bc "import shutil; shutil.rmtree('build', ignore_errors=True)"
	python3 -Bc "import shutil, os.path; shutil.rmtree(os.path.join('source', 'api'), ignore_errors=True)"
	python3 -Bc "import shutil; shutil.rmtree('README.md', ignore_errors=True)"
	python3 -Bc "import shutil, os.path; shutil.rmtree(os.path.join('source', 'screnshots'), ignore_errors=True)"

.PHONY: Makefile
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
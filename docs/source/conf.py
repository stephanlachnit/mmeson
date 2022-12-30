# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
Configuration for the sphinx documentation.
"""

# pylint: disable=invalid-name


import pathlib
import shutil
import sys

import pkg_resources


# a couple of folders
docssrcdir = pathlib.Path(__file__).resolve().parent
repodir = docssrcdir.parents[1]
srcdir = repodir.joinpath('src')
moduledir = srcdir.joinpath('mmeson')

# add folder with module source to sys.path
sys.path.insert(0, srcdir.as_posix())

# copy README and screenshots
shutil.copy(repodir.joinpath('README.md'), docssrcdir)
shutil.copytree(repodir.joinpath('screenshots'), docssrcdir.joinpath('screenshots'), dirs_exist_ok=True)

# project metadata
distribution = pkg_resources.get_distribution('mmeson')
project = distribution.project_name
project_copyright = '2022 Stephan Lachnit, CC-BY-SA-4.0'
author = 'Stephan Lachnit'
version = distribution.version
release = distribution.version

# extensions
extensions = [
    'myst_parser',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.apidoc',
    'sphinx_paramlinks',
]

# general settings
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# HTML settings
html_theme = 'sphinx_rtd_theme'

# sphinx.ext.autosectionlabel settings
autosectionlabel_prefix_document = True

# sphinx.ext.autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': True,
}

# sphinx.ext.intersphinx settings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'urwid': ('http://urwid.org/', None),
}

# sphinxcontrib.apidoc settings
apidoc_module_dir = moduledir.as_posix()
apidoc_separate_modules = True
apidoc_extra_args = ['--ext-intersphinx']  # urwid refs still don,t work

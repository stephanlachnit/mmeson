# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
mmeson is a ccmake clone for Meson projects.
"""

import pkg_resources

__version__ = 'version-unknown'
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except pkg_resources.DistributionNotFound:
    pass  # running from source folder without installation, run "make" or "setup.py egg_info" to create distribution

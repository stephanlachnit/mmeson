# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
mmeson is a ccmake clone for Meson projects.
"""

import pkg_resources

__version__ = pkg_resources.get_distribution(__name__).version

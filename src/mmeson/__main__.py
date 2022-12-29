# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
Entry point for module calling the CLI.
"""

import sys

from .cli import main

if __name__ == '__main__':
    main(sys.argv)

# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
Command-line interface module.
"""

import argparse
import pathlib
import sys

from . import __version__
from .meson_interface import MesonManager
from .options import OptionsManager
from .tui import build_ui, main_loop


def parse_args(args: list[str]) -> argparse.Namespace:
    """
    Parses arguments passed to the CLI. Arguments must start with the first "real" arg, i.e. without executable.

    Args:
        args: :obj:`list` of :obj:`str` to parse as command-line arguments.

    Returns:
        :obj:`argparse.Namespace` with the parsed arguments containing ``builddir`` and ``bin``.
    """
    parser = argparse.ArgumentParser(description='ccmake-like TUI for Meson projects', prog='mmeson',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('builddir', type=pathlib.Path)
    parser.add_argument('-b', '--bin', default='meson', help='meson binary')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    return parser.parse_args(args=args)


def main(args: list[str] = None) -> int:
    """
    Runs the command-line interface. Arguments must start with the first "real" arg, i.e. without executable.

    Args:
        args: :obj:`list` of :obj:`str` to parse as command-line arguments. If :obj:`None` then :obj:`sys.argv` is used
              (excluding the first entry which is the executable).
    """
    if args is None:
        args = sys.argv[1:]
    cli_options = parse_args(args)

    meson_manager = MesonManager()
    meson_manager.set_builddir(cli_options.builddir)
    meson_manager.set_meson_bin(cli_options.bin)

    options_manager = OptionsManager()
    options_manager.set_options(meson_manager.parse_buildoptions())
    meson_version = meson_manager.parse_meson_version()
    project_name, project_version = meson_manager.parse_projectinfo()

    tlw = build_ui(project_name, project_version, meson_version)
    return_code = main_loop(tlw)

    return return_code

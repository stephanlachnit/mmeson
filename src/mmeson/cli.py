# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

from . import meson_interface
from .options import OPTIONS_MANAGER
from .tui import build_ui, main_loop


def main(args: list[str]):
    meson_interface.set_builddir(args[1])
    OPTIONS_MANAGER.set_options(meson_interface.parse_buildoptions())
    meson_version = meson_interface.parse_meson_version()
    project_name, project_version = meson_interface.parse_projectinfo()
    tlw = build_ui(project_name, project_version, meson_version)
    main_loop(tlw)

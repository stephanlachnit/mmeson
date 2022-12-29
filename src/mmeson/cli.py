# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

from .meson_interface import MesonManager
from .options import OptionsManager
from .tui import build_ui, main_loop


def main(args: list[str]):
    meson_manager = MesonManager()
    meson_manager.set_builddir(args[1])
    options_manager = OptionsManager()
    options_manager.set_options(meson_manager.parse_buildoptions())
    meson_version = meson_manager.parse_meson_version()
    project_name, project_version = meson_manager.parse_projectinfo()
    tlw = build_ui(project_name, project_version, meson_version)
    main_loop(tlw)

from . import meson_interface
from .tui import build_ui, main_loop
from .options import options_manager

def main(args: list[str]):
    meson_interface.set_builddir(args[1])
    options_manager.set_options(meson_interface.parse_buildoptions())
    meson_version = meson_interface.parse_meson_version()
    project_name, project_version = meson_interface.parse_projectinfo()
    tlw = build_ui(project_name, project_version, meson_version)
    main_loop(tlw)

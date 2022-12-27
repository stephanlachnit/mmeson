# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

import json
import pathlib
import subprocess

from .options import Option, MesonType, MesonSection, MesonMachine, OPTIONS_MANAGER

# global: builddir variable
_BUILDDIR = pathlib.Path()


def set_builddir(builddir: pathlib.Path | str):
    global _BUILDDIR
    if builddir is not pathlib.Path:
        builddir = pathlib.Path(builddir)
    _BUILDDIR = builddir


def _get_intro_file(intro_file: str) -> dict:
    intro_file_path = pathlib.Path(_BUILDDIR, 'meson-info', intro_file)
    if not intro_file_path.exists():
        raise FileNotFoundError(f'File {intro_file_path.as_posix()} does not exist')
    with open(intro_file_path, mode='rt', encoding='utf-8') as file_io:
        return json.loads(file_io.read())


def parse_buildoptions() -> list[Option]:
    intro_dict = _get_intro_file('intro-buildoptions.json')
    options = list[Option]()
    for entry in intro_dict:
        name = entry['name']
        value = entry['value']
        type = MesonType(entry['type'])
        description = entry['description'] if 'description' in entry else None
        choices = entry['choices'] if 'choices' in entry else None
        section = MesonSection(entry['section'])
        machine = MesonMachine(entry['machine'])
        options.append(Option(name, value, type, description, choices, section, machine))
    return options


def parse_projectinfo() -> tuple[str, str]:
    intro_dict = _get_intro_file('intro-projectinfo.json')
    project_name = intro_dict['descriptive_name']
    project_version = intro_dict['version']
    return (project_name, project_version)


def parse_meson_version() -> str:
    intro_dict = _get_intro_file('meson-info.json')
    return intro_dict['meson_version']['full']


def parse_meson_workdir() -> pathlib.Path:
    intro_dict = _get_intro_file('meson-info.json')
    return pathlib.Path(intro_dict['directories']['source'])


def run_meson_configure():
    unmodified_options = OPTIONS_MANAGER.get_modified_options()
    if len(unmodified_options) == 0:
        print('Nothing to configure!')
    else:
        config_args = list[str]()
        for option in unmodified_options:
            config_args.append(f'-D{option.name}={option.value_as_string()}')
        print(config_args)
        cwd = parse_meson_workdir()
        subprocess.run(['meson', 'configure', _BUILDDIR.as_posix()] + config_args, cwd=cwd, check=False)
        subprocess.run(['meson', 'setup', '--reconfigure', _BUILDDIR.as_posix()], cwd=cwd, check=False)

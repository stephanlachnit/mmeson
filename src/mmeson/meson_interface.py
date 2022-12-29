# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

import enum
import json
import pathlib
import subprocess

from .options import Option, OptionsManager, MesonType, MesonSection, MesonMachine
from .singleton import Singleton


class ExitAction(enum.StrEnum):
    NOTHING = 'nothing'
    ONLY_CONFIGURE = 'only-configure'
    RECONFIGURE = 'reconfigure'


class MesonManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.builddir = pathlib.Path()
        self.exit_action = ExitAction.NOTHING

    def set_builddir(self, builddir: pathlib.Path | str):
        if self.builddir is not pathlib.Path:
            self.builddir = pathlib.Path(builddir)
        if not self.builddir.is_dir():
            raise Exception(f'{self.builddir.as_posix()} is not a directory')

    def _get_intro_file(self, intro_file: str) -> dict:
        intro_file_path = pathlib.Path(self.builddir, 'meson-info', intro_file)
        if not intro_file_path.exists():
            raise FileNotFoundError(f'File {intro_file_path.as_posix()} does not exist')
        with open(intro_file_path, mode='rt', encoding='utf-8') as file_io:
            return json.loads(file_io.read())

    def parse_buildoptions(self) -> list[Option]:
        intro_dict = self._get_intro_file('intro-buildoptions.json')
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

    def parse_projectinfo(self) -> tuple[str, str]:
        intro_dict = self._get_intro_file('intro-projectinfo.json')
        project_name = intro_dict['descriptive_name']
        project_version = intro_dict['version']
        return (project_name, project_version)

    def parse_meson_version(self) -> str:
        intro_dict = self._get_intro_file('meson-info.json')
        return intro_dict['meson_version']['full']

    def parse_meson_workdir(self) -> pathlib.Path:
        intro_dict = self._get_intro_file('meson-info.json')
        return pathlib.Path(intro_dict['directories']['source'])

    def set_exit_action(self, exit_action: ExitAction):
        self.exit_action = exit_action

    def run_exit_action(self):
        options_manager = OptionsManager()
        modified_options = options_manager.get_modified_options()
        modified_options_count = len(modified_options)

        if self.exit_action == ExitAction.NOTHING:
            if modified_options_count != 0:
                print(f'Ignoring {modified_options_count} changes')
            return

        if modified_options_count == 0:
            print('Nothing to configure!')
            return

        print(f'Configuring {modified_options_count} changes')
        config_args = list[str]()
        for option in modified_options:
            config_args.append(f'-D{option.name}={option.value_as_string()}')

        cwd = self.parse_meson_workdir()
        subprocess.run(['meson', 'configure', self.builddir.as_posix()] + config_args, cwd=cwd, check=False)

        if self.exit_action == ExitAction.RECONFIGURE:
            print('Reconfiguring project')
            subprocess.run(['meson', 'setup', '--reconfigure', self.builddir.as_posix()], cwd=cwd, check=False)

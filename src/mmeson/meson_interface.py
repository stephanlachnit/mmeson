# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
Module containing Meson-related classes and funtions.
"""

import enum
import json
import pathlib
import subprocess

from .options import Option, OptionsManager, MesonType, MesonSection, MesonMachine
from .singleton import Singleton


class ExitAction(enum.Enum):
    """
    Enum for the exit action. TODO more explaination.
    """

    NOTHING = 'nothing'
    """Exit without saving the changed config values."""

    ONLY_CONFIGURE = 'only-configure'
    """Exit without saving the changed config values."""

    RECONFIGURE = 'reconfigure'
    """Same as :attr:`ONLY_CONFIGURE` but calls ``meson setup --reconfigure`` afterwards."""


class MesonManager(metaclass=Singleton):
    """
    Singleton class managing Meson-related parsing and actions.

    Attributes:
        builddir: :class:`pathlib.Path` containing the builddir (has to be set via :func:`set_builddir()`).
        meson_bin: :obj:`str` pointing to the Meson binary (has to be set via :func:`set_meson_bin()`).
        exit_action: see :class:`ExitAction` for details.
    """
    def __init__(self) -> None:
        self.builddir = pathlib.Path()
        self.meson_bin = str()
        self.exit_action = ExitAction.NOTHING

    def set_builddir(self, builddir: pathlib.Path):
        """
        Sets the builddir of the Meson project.

        Args:
            builddir: :class:`pathlib.Path` pointing to the builddir.
        """
        self.builddir = builddir
        if not self.builddir.is_dir():
            raise Exception(f'{self.builddir.as_posix()} is not a directory')

    def set_meson_bin(self, meson_bin: str):
        """
        Sets the Meson binary to use.

        Args:
            meson_bin: Name of the Meson binary in ``PATH`` or path to Meson binary as :obj:`str`.
        """
        self.meson_bin = meson_bin

    def get_intro_file(self, intro_file: str) -> dict:
        """
        Loads and introspection file from the ``meson-info`` folder and parses the json into a :obj:`dict`.

        Args:
            intro_file: Name of the introspection file.

        Returns:
            The dict contained in the introspection file.
        """
        intro_file_path = pathlib.Path(self.builddir, 'meson-info', intro_file)
        if not intro_file_path.exists():
            raise FileNotFoundError(f'File {intro_file_path.as_posix()} does not exist')
        with open(intro_file_path, mode='rt', encoding='utf-8') as file_io:
            return json.loads(file_io.read())

    def parse_buildoptions(self) -> list[Option]:
        """
        Parses the build options given by Meson in the builddir.

        Returns:
            List of :class:`~.options.Option` parsed from the builddir.
        """
        intro_dict = self.get_intro_file('intro-buildoptions.json')
        options = list[Option]()
        for entry in intro_dict:
            name = entry['name']
            value = entry['value']
            value_type = MesonType(entry['type'])
            description = entry['description'] if 'description' in entry else None
            choices = entry['choices'] if 'choices' in entry else None
            section = MesonSection(entry['section'])
            machine = MesonMachine(entry['machine'])
            options.append(Option(name, value, value_type, description, choices, section, machine))
        return options

    def parse_projectinfo(self) -> tuple[str, str]:
        """
        Parses the project info given by Meson in the builddir.

        Returns:
            Tuple of strings containing the project name and project version.
        """
        intro_dict = self.get_intro_file('intro-projectinfo.json')
        project_name = intro_dict['descriptive_name']
        project_version = intro_dict['version']
        return (project_name, project_version)

    def parse_meson_version(self) -> str:
        """
        Parses the meson version given by Meson in the builddir.

        Returns:
            String containing the used meson version.
        """
        intro_dict = self.get_intro_file('meson-info.json')
        return intro_dict['meson_version']['full']

    def parse_meson_workdir(self) -> pathlib.Path:
        """
        Parses the meson source folder given by Meson in the builddir.

        Returns:
            :class:`pathlib.Path` containing path to the source folder.
        """
        intro_dict = self.get_intro_file('meson-info.json')
        return pathlib.Path(intro_dict['directories']['source'])

    def set_exit_action(self, exit_action: ExitAction) -> None:
        """
        Sets the action to be done when :func:`run_exit_action()` is called.

        Args:
            exit_action: see :class:`ExitAction` for details.
        """
        self.exit_action = exit_action

    def run_exit_action(self) -> int:
        """
        Runs the exit action. For exact behaviour see :class:`ExitAction` for details.

        Returns:
            Return code from the last Meson call or ``0`` if Meson is never called.
        """
        options_manager = OptionsManager()
        modified_options = options_manager.get_modified_options()
        modified_options_count = len(modified_options)

        if self.exit_action == ExitAction.NOTHING:
            if modified_options_count != 0:
                print(f'Ignoring {modified_options_count} changes')
            return 0

        if modified_options_count == 0:
            print('Nothing to configure!')
            return 0

        print(f'Configuring {modified_options_count} changes')
        config_args = list[str]()
        for option in modified_options:
            config_args.append(f'-D{option.name}={option.value_as_string()}')

        cwd = self.parse_meson_workdir()
        meson_configure_args = [self.meson_bin, 'configure', self.builddir.as_posix()] + config_args
        meson_configure_proc = subprocess.run(meson_configure_args, cwd=cwd, check=False)

        if self.exit_action == ExitAction.ONLY_CONFIGURE:
            return meson_configure_proc.returncode

        if meson_configure_proc.returncode != 0:
            print('Configuration failed, skipping reconfiguration!')
            return meson_configure_proc.returncode

        print('Reconfiguring project')
        meson_reconfigure_args = [self.meson_bin, 'setup', '--reconfigure', self.builddir.as_posix()]
        meson_reconfigure_proc = subprocess.run(meson_reconfigure_args, cwd=cwd, check=False)
        return meson_reconfigure_proc.returncode

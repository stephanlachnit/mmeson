# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
Module containing definitions of Meson's option format and the :class:`OptionsManager`.
"""

import enum

from .singleton import Singleton


class MesonType(enum.StrEnum):
    """
    Enum for Meson's option type. See `Meson's manual`__ for details.

    .. __: https://mesonbuild.com/Build-options.html
    """
    STRING = 'string'
    BOOLEAN = 'boolean'
    COMBO = 'combo'
    INTEGER = 'integer'
    ARRAY = 'array'


class MesonSection(enum.StrEnum):
    """
    Enum for Meson's option section. See `Meson's manual`__ for details.

    .. __: https://mesonbuild.com/IDE-integration.html
    """
    CORE = 'core'
    BACKEND = 'backend'
    BASE = 'base'
    COMPILER = 'compiler'
    DIRECTORY = 'directory'
    USER = 'user'
    TEST = 'test'


class MesonMachine(enum.StrEnum):
    """
    Enum for Meson's machine entry. See `Meson's manual`__ for details.

    .. __: https://mesonbuild.com/Cross-compilation.html
    """
    ANY = 'any'
    HOST = 'host'
    BUILD = 'build'


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-few-public-methods
class Option():
    """
    Class containing the attributes of a Meson option. See `Meson's manual`__ for details.

    .. __: https://mesonbuild.com/Build-options.html
    """
    def __init__(self,
                 name: str, value, value_type: MesonType, description: str, choices: list[str],
                 section: MesonSection, machine: MesonMachine):
        self.name = name
        self.value = value
        self.type = value_type
        self.description = description
        self.choices = choices
        self.section = section
        self.machine = machine
        self.modified = False

    # pylint: disable=inconsistent-return-statements
    def value_as_string(self) -> str:
        """
        Converts the option value to a string such that it can be used to be passed to Meson's CLI.

        Returns:
            Option value formatted as string.
        """
        if self.type == MesonType.STRING:
            return f'"{self.value}"'
        if self.type == MesonType.BOOLEAN:
            return repr(self.value).lower()
        if self.type == MesonType.COMBO:
            return self.value
        if self.type == MesonType.INTEGER:
            return str(self.value)
        if self.type == MesonType.ARRAY:
            ret = '['
            for entry in self.value:
                ret += f'\'{entry}\','
            ret = ret[:-1] + ']'
            return ret


class OptionsManager(metaclass=Singleton):
    """
    Singleton class owning the list of all options.

    Attributes:
        options: :obj:`list` of :class:`Option` list of all current options.
    """
    def __init__(self):
        self.options = list[Option]()

    def set_options(self, options: list[Option]) -> None:
        """
        Sets the :attr:`options` member and sorts it.

        Args:
            options: List of options to use for :attr:`options` member.
        """
        def sorter(option: Option) -> tuple[str, int, str]:
            """
            Sorting with highest priority to subproject name, then the section with a custom ordering and only then the
            name of the option.
            """
            section_map = {
                MesonSection.USER: 1,
                MesonSection.BASE: 2,
                MesonSection.COMPILER: 3,
                MesonSection.CORE: 4,
                MesonSection.DIRECTORY: 5,
                MesonSection.TEST: 6,
                MesonSection.BACKEND: 7,
            }
            splitted = option.name.split(':')
            subproject = '' if len(splitted) == 1 else splitted[0]
            option_name = splitted[0] if len(splitted) == 1 else splitted[1]
            return (subproject, section_map[option.section], option_name)
        self.options = sorted(options, key=sorter)

    def get_options(self) -> list[Option]:
        """
        Returns:
            List of all options.
        """
        return self.options

    def get_option(self, index: int) -> Option:
        """
        Args:
            index: index of the option in the :attr:`options` list.

        Returns:
            :class:`Option` from the :attr:`options` list.
        """
        return self.options[index]

    def get_modified_options(self) -> list[Option]:
        """
        Returns:
            List of all modified options.
        """
        return list(filter(lambda option: option.modified, self.options))

    def set_modified(self, index: int, value) -> None:
        """
        Modify an option and mark it as modified.

        Args:
            index: index of the option in the :attr:`options` list.
            value: value to set according to the option's :class:`MesonType`.
        """
        self.options[index].modified = True
        self.options[index].value = value

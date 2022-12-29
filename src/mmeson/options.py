# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

import enum

from .singleton import Singleton


class MesonType(enum.StrEnum):
    STRING = 'string'
    BOOLEAN = 'boolean'
    COMBO = 'combo'
    INTEGER = 'integer'
    ARRAY = 'array'


class MesonSection(enum.StrEnum):
    CORE = 'core'
    BACKEND = 'backend'
    BASE = 'base'
    COMPILER = 'compiler'
    DIRECTORY = 'directory'
    USER = 'user'
    TEST = 'test'


class MesonMachine(enum.StrEnum):
    ANY = 'any'
    HOST = 'host'
    BUILD = 'build'


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-few-public-methods
class Option():
    def __init__(self,
                 name: str, value, type: MesonType, description: str, choices: list[str],
                 section: MesonSection, machine: MesonMachine):
        self.name = name
        self.value = value
        self.type = type
        self.description = description
        self.choices = choices
        self.section = section
        self.machine = machine
        self.modified = False

    # pylint: disable=inconsistent-return-statements
    def value_as_string(self) -> str:
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
    def __init__(self):
        self._options = list[Option]()

    def set_options(self, options: list[Option]):
        def sorter(option: Option):
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
        self._options = sorted(options, key=sorter)

    def get_options(self) -> list[Option]:
        return self._options

    def get_option(self, index: int) -> Option:
        return self._options[index]

    def get_modified_options(self) -> list[Option]:
        return list(filter(lambda option: option.modified, self._options))

    def set_modified(self, index: int, value) -> None:
        self._options[index].modified = True
        self._options[index].value = value

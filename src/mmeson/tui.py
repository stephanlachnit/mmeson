# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

from ast import literal_eval

import urwid

from .meson_interface import MesonManager, ExitAction
from .options import Option, OptionsManager, MesonType


PALETTE = [
    ('true', 'dark green', ''),
    ('false', 'dark red', ''),
    ('choice', 'light blue', ''),
    ('enabled', 'dark green', ''),
    ('disabled', 'dark red', ''),
    ('string', 'yellow', ''),
    ('integer', 'light magenta', ''),
    ('array', 'brown', ''),
]


class MesonEdit(urwid.AttrMap):
    signals = ['changed']

    def __init__(self, widget: urwid.Widget, attr_map):
        super().__init__(widget, attr_map)

    def get_value(self):
        return None


class StringEdit(MesonEdit):
    def __init__(self, value: str, attr_map='string'):
        self.activated = False
        widget = urwid.Edit('', value, multiline=False, edit_pos=0, wrap=urwid.CLIP)
        super().__init__(widget, attr_map)

    def get_value(self) -> str:
        return self.original_widget.get_text()[0]

    # pylint: disable=inconsistent-return-statements
    def keypress(self, size, key):
        if key == 'enter':
            self.activated = not self.activated
            edit_pos = len(self.original_widget.get_text()[0]) if self.activated else 0
            self.original_widget.set_edit_pos(edit_pos)
            if not self.activated:
                urwid.emit_signal(self, 'changed')
        else:
            if self.activated:
                self.original_widget.keypress(size, key)
            else:
                return key


class BooleanEdit(MesonEdit):
    def __init__(self, init_state: bool):
        self._state = init_state
        widget = urwid.SelectableIcon(repr(init_state))
        super().__init__(widget, repr(init_state).lower())

    def set_state(self, state: bool):
        if self._state == state:
            return
        self._state = state
        self.original_widget.set_text(repr(state))
        self.set_attr_map({None: repr(state).lower()})
        urwid.emit_signal(self, 'changed')

    def get_value(self):
        return self._state

    def toggle_state(self):
        self.set_state(not self._state)

    # pylint: disable=inconsistent-return-statements,unused-argument
    def keypress(self, size, key):
        if self._command_map[key] != urwid.ACTIVATE:
            return key
        self.toggle_state()


class ComboEdit(MesonEdit):
    def __init__(self, init_choice: str, choices: list[str]):
        self._choice_index = choices.index(init_choice)
        self._choices = choices
        widget = urwid.SelectableIcon(init_choice)
        super().__init__(widget, self.create_attr_map(init_choice))

    @staticmethod
    def create_attr_map(choice: str):
        if choice in ['enabled', 'disabled', 'true', 'false']:
            return {None: choice}
        return {None: 'choice'}

    def set_choice(self, choice_index: int):
        if self._choice_index == choice_index:
            return
        self._choice_index = choice_index
        choice = self.get_choice()
        self.original_widget.set_text(choice)
        self.set_attr_map(self.create_attr_map(choice))
        urwid.emit_signal(self, 'changed')

    def get_choice(self) -> str:
        return self._choices[self._choice_index]

    def get_value(self) -> str:
        return self.get_choice()

    def rotate_choice(self):
        if self._choice_index == len(self._choices) - 1:
            self.set_choice(0)
        else:
            self.set_choice(self._choice_index + 1)

    # pylint: disable=inconsistent-return-statements,unused-argument
    def keypress(self, size, key):
        if self._command_map[key] != urwid.ACTIVATE:
            return key
        self.rotate_choice()


class IntegerEdit(MesonEdit):
    def __init__(self, value: int):
        self.activated = False
        widget = urwid.IntEdit('', value)
        super().__init__(widget, 'integer')

    def get_value(self) -> int:
        return self.original_widget.value()

    # pylint: disable=inconsistent-return-statements
    def keypress(self, size, key):
        if key == 'enter':
            self.activated = not self.activated
            if not self.activated:
                urwid.emit_signal(self, 'changed')
        else:
            if self.activated:
                self.original_widget.keypress(size, key)
            else:
                return key


class ArrayEdit(StringEdit):
    def __init__(self, value: list[str]):
        super().__init__(str(value), 'array')

    def get_value(self) -> list[str]:
        return literal_eval(super().get_value())


class OptionRow(urwid.Columns):
    def __init__(self, option: Option):
        self.changed = False
        self.name_widget = urwid.Text(option.name, urwid.LEFT, urwid.CLIP)
        self.value_widget = self._build_value_widget(option)
        widget_list = [(urwid.WEIGHT, 40, self.name_widget), (urwid.WEIGHT, 60, self.value_widget)]
        super().__init__(widget_list, dividechars=1, focus_column=1)

    # pylint: disable=inconsistent-return-statements
    @staticmethod
    def _build_value_widget(option: Option) -> MesonEdit:
        if option.type == MesonType.STRING:
            return StringEdit(option.value)
        if option.type == MesonType.BOOLEAN:
            return BooleanEdit(option.value)
        if option.type == MesonType.COMBO:
            return ComboEdit(option.value, option.choices)
        if option.type == MesonType.INTEGER:
            return IntegerEdit(option.value)
        if option.type == MesonType.ARRAY:
            return ArrayEdit(option.value)

    def set_changed(self):
        if self.changed:
            return
        self.changed = True
        self.name_widget.set_text('*' + self.name_widget.get_text()[0])

    def get_value(self):
        return self.value_widget.get_value()


class OptionList(urwid.ListBox):
    signals = ['focus-modified']

    def __init__(self):
        self._option_rows = self._build_option_rows()
        self._walker = urwid.SimpleFocusListWalker(self._option_rows)
        super().__init__(self._walker)
        urwid.connect_signal(self._walker, 'modified', self.focus_modified_callback)

    def _build_option_rows(self) -> list[OptionRow]:
        option_manager = OptionsManager()
        option_rows = list[OptionRow]()
        for index, option in enumerate(option_manager.get_options()):
            option_row = OptionRow(option)
            option_rows.append(option_row)
            urwid.connect_signal(
                option_row.value_widget, 'changed', self._entry_modified_callback, user_args=[option_row, index])
        return option_rows

    def focus_modified_callback(self):
        option_index = self._walker.get_focus()[1]
        urwid.emit_signal(self, 'focus-modified', option_index)

    @staticmethod
    def _entry_modified_callback(option_row: OptionRow, option_index: int) -> None:
        option_row.set_changed()
        option_manager = OptionsManager()
        option_manager.set_modified(option_index, option_row.get_value())


class Header(urwid.Text):
    def __init__(self, project_name: str, project_version: str, meson_version: str):
        text = f'Build options for {project_name} {project_version} (Meson {meson_version})'
        super().__init__(text, align=urwid.CENTER)


class Footer(urwid.Pile):
    def __init__(self):
        divider = urwid.Divider()
        self.text_info = urwid.Text('\n\n', wrap=urwid.CLIP)
        text_help_str = 'Keys: [enter] Edit entry [c] Reconfigure [g] Configure [q] Quit'
        text_help = urwid.Text(text_help_str, wrap=urwid.CLIP)
        super().__init__([divider, self.text_info, text_help])

    def option_list_callback(self, option_index: int):
        options_manager = OptionsManager()
        option = options_manager.get_option(option_index)
        choices_str = ''
        if option.choices is not None:
            choices_str = 'Choices:'
            for choice in option.choices:
                choices_str += f' {choice}'
        text_l1 = f'{option.name}: {option.description}'
        text_l2 = f'Section: {option.section}, Machine: {option.machine}, Type: {option.type}'
        self.text_info.set_text(f'{text_l1}\n{text_l2}\n{choices_str}')


def build_ui(project_name: str, project_version: str, meson_version: str):
    header = Header(project_name, project_version, meson_version)
    footer = Footer()
    body = OptionList()
    urwid.connect_signal(body, 'focus-modified', footer.option_list_callback)
    body.focus_modified_callback()  # initial setting for footer
    frame = urwid.Frame(body, header, footer)
    return frame


def global_key_handler(key: str):
    meson_manager = MesonManager()
    if key in ('q', 'Q'):
        meson_manager.set_exit_action(ExitAction.NOTHING)
        raise urwid.ExitMainLoop()
    if key in ('c', 'C'):
        meson_manager.set_exit_action(ExitAction.RECONFIGURE)
        raise urwid.ExitMainLoop()
    if key in ('g', 'G'):
        meson_manager.set_exit_action(ExitAction.ONLY_CONFIGURE)
        raise urwid.ExitMainLoop()


def main_loop(top_level_widget: urwid.Widget):
    loop = urwid.MainLoop(top_level_widget, palette=PALETTE, unhandled_input=global_key_handler, handle_mouse=False)
    try:
        loop.run()
    except KeyboardInterrupt:
        urwid.ExitMainLoop()
    meson_manager = MesonManager()
    meson_manager.run_exit_action()

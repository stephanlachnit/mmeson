# SPDX-FileCopyrightText: 2022 Stephan Lachnit <stephanlachnit@debian.org>
# SPDX-License-Identifier: EUPL-1.2

"""
Module implementing the urwid TUI (terminal user interface).

If you are unfamilir with urwid, take a look at the excellent documentation at http://urwid.org/.

The basic design consits of a :class:`urwid.Frame` with :class:`Header` as header and :class:`Footer` as footer. The
body consits of :class:`OptionList`, which is a :class:`urwid.ListBox` containing the :class:`OptionRow` widgets. The
:class:`urwid.ListBox` widget requires a :class:`urwid.SimpleFocusListWalker`, which emits a ``modified`` signal when
the focused :class:`OptionRow` changes. This is used to update the information in the :class:`Footer`.

The :class:`OptionRow` is a :class:`urwid.Columns` with a :class:`urwid.Text` showing the option name on the left and
a custom :class:`MesonEdit` widget on the to change the option value.

Currently, the :class:`MesonEdit` class is a subclass of :class:`urwid.AttrMap` to force the colored output, but this
is a just an ugly workaround, in theory using TextMarkup (http://urwid.org/manual/displayattributes.html#text-markup)
should suffice.
"""

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
"""Color Palette, see `urwid's manual`__ for details.

.. __: http://urwid.org/manual/displaymodules.html#setting-a-palette"""


class MesonEdit(urwid.AttrMap):
    """
    Virtual widget class for editing option values.

    Args:
        widget: :class:`urwid.Widget` to
        attr_map: :obj:`dict` or :obj:`str` for :class:`urwid.AttrMap`. Workaround to change the color of the widget.
    """

    signals = ['changed']
    """:obj:`list` of :mod:`urwid` signal names the class can emit."""

    def __init__(self, widget: urwid.Widget, attr_map: dict | str):
        super().__init__(widget, attr_map)

    def get_value(self):
        """
        Virtual function to return the value contained in the widget.
        """
        return None


class StringEdit(MesonEdit):
    """
    :class:`MesonEdit` widget to modify :class:`~.Option` of type :attr:`~.MesonType.STRING`.
    Uses :class:`urwid.Edit` as base.

    Args:
        value: Initial value of the widget.
        attr_map: Text color from :obj:`~.PALETTE`, mainly for :class:`ArrayEdit`.

    Attributes:
        activated: :obj:`bool` that control whether input is used for editing or not. See :func:`keypress`.
    """
    def __init__(self, value: str, attr_map='string'):
        self.activated = False
        widget = urwid.Edit('', value, multiline=False, edit_pos=0, wrap=urwid.CLIP)
        super().__init__(widget, attr_map)

    def get_value(self) -> str:
        """
        Returns:
            Value of the widget as :obj:`str`.
        """
        return self.original_widget.get_text()[0]

    # pylint: disable=inconsistent-return-statements
    def keypress(self, size, key):
        """
        Keypress handler for this widget.

        The widget needs to be activated to forward keypresses. This is handled via the :attr:`activated` member, which
        is toggled when ``enter`` is pressed. If the :attr:`activated` is :obj:`True`, keypresses are forwarded to the
        containing widget (:class:`urwid.Edit`). Additionally, when the :attr:`activated` member is changed from
        :obj:`True` to :obj:`False`, a ``changed`` signal is emitted. If :attr:`activated` is :obj:`False`,
        :paramref:`~keypress.key` is returned. This tells :mod:`urwid` that it is not used by the widget.

        Args:
            size: unused (given from :mod:`urwid`).
            key: key name (given from :mod:`urwid`).
        """
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
    """
    :class:`MesonEdit` widget to modify :class:`~.Option` of type :attr:`~.MesonType.BOOLEAN`.
    Uses :class:`urwid.SelectableIcon` as base.

    Args:
        init_state: value for the initial value of :attr:`state`.

    Attributes:
        state: :obj:`bool` of the current value.
    """
    def __init__(self, init_state: bool):
        self.state = init_state
        widget = urwid.SelectableIcon(repr(init_state))
        super().__init__(widget, repr(init_state).lower())

    def set_state(self, state: bool) -> None:
        """
        Set a new state, change color of the :class:`urwid.AttrMap` and emit a ``changed`` signal.

        Args:
            state: :obj:`bool` of the new state.
        """
        if self.state == state:
            return
        self.state = state
        self.original_widget.set_text(repr(state))
        self.set_attr_map({None: repr(state).lower()})
        urwid.emit_signal(self, 'changed')

    def get_value(self) -> bool:
        """
        Returns:
            Value of the widget as :obj:`bool`.
        """
        return self.state

    def toggle_state(self) -> None:
        """
        Toggle the current state.
        """
        self.set_state(not self.state)

    # pylint: disable=inconsistent-return-statements,unused-argument
    def keypress(self, size, key):
        """
        Keypress handler for this widget. Taken from :class:`urwid.CheckBox`.

        Args:
            size: unused (given from :mod:`urwid`).
            key: key name (given from :mod:`urwid`).
        """
        if self._command_map[key] != urwid.ACTIVATE:
            return key
        self.toggle_state()


class ComboEdit(MesonEdit):
    """
    :class:`MesonEdit` widget to modify :class:`~.Option` of type :attr:`~.MesonType.COMBO`.
    Uses :class:`urwid.SelectableIcon` as base.

    Args:
        init_choice: Value used for the initial value of :attr:`choice_index`.
        choices: List of valid choices.

    Attributes:
        choice_index: :obj:`int` refering to the index of the currently selected choice.
        choices: List of valid choices.
    """
    def __init__(self, init_choice: str, choices: list[str]):
        self.choice_index = choices.index(init_choice)
        self.choices = choices
        widget = urwid.SelectableIcon(init_choice)
        super().__init__(widget, self.create_attr_map(init_choice))

    def create_attr_map(self, choice: str) -> dict:
        """
        Creates an attribute map for the widget. Workaround to adjust the color of the widget depending on the choice.
        For ``enabled``, ``true``, ``disabled`` and ``false`` the color is defined in :obj:`PALETTE`, for other choices
        use the ``choice`` color defined in :obj:`PALETTE`.

        Args:
            choice: choice to return color / attribute :obj:`dict` for.

        Returns:
            :obj:`dict` formatted as ``{None: 'color_name'}``.
        """
        if choice in ['enabled', 'true', 'disabled', 'false']:
            return {None: choice}
        return {None: 'choice'}

    def set_choice(self, choice_index: int) -> None:
        """
        Set a new choice, change color of the :class:`urwid.AttrMap` and emit a ``changed`` signal.

        Args:
            choice_index: :obj:`int` new choice index for :attr:`choice_index`.
        """
        if self.choice_index == choice_index:
            return
        self.choice_index = choice_index
        choice = self.get_choice()
        self.original_widget.set_text(choice)
        self.set_attr_map(self.create_attr_map(choice))
        urwid.emit_signal(self, 'changed')

    def get_choice(self) -> str:
        """
        Returns:
            Current selected choice as :obj:`str`.
        """
        return self.choices[self.choice_index]

    def get_value(self) -> str:
        """
        Returns:
            Value of the widget as :obj:`str`.
        """
        return self.get_choice()

    def rotate_choice(self) -> None:
        """
        Select next choice in :attr:`choices` list.
        """
        if self.choice_index == len(self.choices) - 1:
            self.set_choice(0)
        else:
            self.set_choice(self.choice_index + 1)

    # pylint: disable=inconsistent-return-statements,unused-argument
    def keypress(self, size, key):
        """
        Keypress handler for this widget. Same as :func:`BooleanEdit.keypress`.
        """
        if self._command_map[key] != urwid.ACTIVATE:
            return key
        self.rotate_choice()


class IntegerEdit(MesonEdit):
    """
    :class:`MesonEdit` widget to modify :class:`~.Option` of type :attr:`~.MesonType.INTEGER`.
    Uses :class:`urwid.IntEdit` as base.

    Args:
        value: Initial value of the widget.

    Attributes:
        activated: See :attr:`StringEdit.activated`.
    """
    def __init__(self, value: int):
        self.activated = False
        widget = urwid.IntEdit('', value)
        super().__init__(widget, 'integer')

    def get_value(self) -> int:
        """
        Returns:
            Value of the widget as :obj:`int`.
        """
        return self.original_widget.value()

    # pylint: disable=inconsistent-return-statements
    def keypress(self, size, key):
        """
        Keypress handler for this widget. Similar to :func:`StringEdit.keypress`.
        """
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
    """
    :class:`MesonEdit` widget to modify :class:`~.Option` of type :attr:`~.MesonType.ARRAY`.
    Uses :class:`StringEdit` as base.

    Args:
        value: Initial value of the widget.
    """
    def __init__(self, value: list[str]):
        super().__init__(str(value), 'array')

    def get_value(self) -> list[str]:
        """
        Returns:
            Value of the widget as :obj:`list` of :obj:`str`.
        """
        return literal_eval(super().get_value())


class OptionRow(urwid.Columns):
    """
    Widget for a single row in the :class:`OptionList`, consiting of a `urwid.Text` widget on the left (40% width) and
    a :class:`MesonEdit` widget on the right (60% width).

    Args:
        option: :class:`~.Option` to build the widget for.

    Attributes:
        changed: :obj:`bool` that will be set to :obj:`True` in :func:`set_changed`.
        name_widget: :class:`urwid.Text` containing the option name on the left.
        value_widget: :class:`MesonEdit` for changing the option value on the right.
    """
    def __init__(self, option: Option):
        self.changed = False
        self.name_widget = urwid.Text(option.name, urwid.LEFT, urwid.CLIP)
        self.value_widget = self.build_value_widget(option)
        widget_list = [(urwid.WEIGHT, 40, self.name_widget), (urwid.WEIGHT, 60, self.value_widget)]
        super().__init__(widget_list, dividechars=1, focus_column=1)

    # pylint: disable=inconsistent-return-statements
    def build_value_widget(self, option: Option) -> MesonEdit:
        """
        Build the corresponding :class:`MesonEdit` subclass depending in the option type.

        Args:
            option: :class:`~.Option` to create the widget for.
        """
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

    def set_changed(self) -> None:
        """
        Adds a ``*`` in front of the option name to indicate the option was changed.
        """
        if self.changed:
            return
        self.changed = True
        self.name_widget.set_text('*' + self.name_widget.get_text()[0])

    def get_value(self):
        """
        Returns:
            Value of the widget (in the option's type).
        """
        return self.value_widget.get_value()


class OptionList(urwid.ListBox):
    """
    Body of the main frame. :class:`urwid.ListBox` containing a :class:`OptionRow` for every :class:`Option`.

    Attributes:
        option_rows: :obj:`list` of :class:`OptionRow` contained in the widget.
        walker: :class:`urwid.SimpleFocusListWalker` managing the focusing of the contained widgets.
    """

    signals = ['focus-modified']
    """:obj:`list` of :mod:`urwid` signal names the class can emit."""

    def __init__(self):
        self.option_rows = self.build_option_rows()
        self.walker = urwid.SimpleFocusListWalker(self.option_rows)
        super().__init__(self.walker)
        urwid.connect_signal(self.walker, 'modified', self.focus_modified_callback)

    def build_option_rows(self) -> list[OptionRow]:
        """
        Creates an :class:`OptionRow` for every :class:`~.Option` from the :class:`~.OptionsManager` and connects their
        ``changed`` signal to :func:`entry_modified_callback` with the widget and index as arguments.

        Returns:
            :obj:`list` of :class:`OptionRow`.
        """
        option_manager = OptionsManager()
        option_rows = list[OptionRow]()
        for index, option in enumerate(option_manager.get_options()):
            option_row = OptionRow(option)
            option_rows.append(option_row)
            urwid.connect_signal(
                option_row.value_widget, 'changed', self.entry_modified_callback, user_args=[option_row, index])
        return option_rows

    def focus_modified_callback(self) -> None:
        """
        Callback for the ``modified`` signal from :attr:`walker`. Forwards the signal as ``focus-modified`` signal with
        the index of the currently focused :class:`OptionRow`.
        """
        option_index = self.walker.get_focus()[1]
        urwid.emit_signal(self, 'focus-modified', option_index)

    def entry_modified_callback(self, option_row: OptionRow, option_index: int) -> None:
        """
        Callback for the ``changed`` signal from an :class:`OptionRow`. Sets the :class:`~.Option` as modified in the
        :class:`~.OptionsManager` with the new value via :func:`MesonEdit.get_value`.
        """
        option_row.set_changed()
        option_manager = OptionsManager()
        option_manager.set_modified(option_index, option_row.get_value())


class Header(urwid.Text):
    """
    Header of the main frame. :class:`urwid.Text` containing the project name, version and the Meson version used to
    configure the project.

    Args:
        project_name: Name of the Meson project.
        project_version: Project version as :obj:`str`.
        meson_version: Meson version as :obj:`str`.

    """
    def __init__(self, project_name: str, project_version: str, meson_version: str):
        text = f'Build options for {project_name} {project_version} (Meson {meson_version})'
        super().__init__(text, align=urwid.CENTER)


class Footer(urwid.Pile):
    """
    Footer of the main frame. :class:`urwid.Pile` a one line divider, a three line info text and a single line help
    text containing the keyboard controls. The third line of the :attr:`text_info` is only filled when choices are
    available.

    Attributes:
        text_info: :class:`urwid.Text` containing the option meta info (see :func:`option_list_callback`).
    """
    def __init__(self):
        divider = urwid.Divider()
        self.text_info = urwid.Text('\n\n', wrap=urwid.CLIP)
        text_help_str = 'Keys: [enter] Edit entry [c] Reconfigure [g] Configure [q] Quit'
        text_help = urwid.Text(text_help_str, wrap=urwid.CLIP)
        super().__init__([divider, self.text_info, text_help])

    def option_list_callback(self, option_index: int) -> None:
        """
        Callback changing the option meta information in the footer.

        Args:
            option_index: index of the option for the :class:`~.OptionsManager`.
        """
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


def build_ui(project_name: str, project_version: str, meson_version: str) -> urwid.Widget:
    """
    Build the TUI tree and returns the top-level widget.

    Args:
        project_name: Name of the Meson project.
        project_version: Project version as :obj:`str`.
        meson_version: Meson version as :obj:`str`.

    Returns:
        Top-level widget of the :mod:`urwid` TUI.
    """
    header = Header(project_name, project_version, meson_version)
    footer = Footer()
    body = OptionList()
    urwid.connect_signal(body, 'focus-modified', footer.option_list_callback)
    body.focus_modified_callback()  # initial setting for footer
    frame = urwid.Frame(body, header, footer)
    return frame


def global_key_handler(key: str) -> None:
    """
    Global key handler for unhandled key presses.

    Args:
        key: key name (given from :mod:`urwid`).
    """
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


def main_loop(top_level_widget: urwid.Widget) -> int:
    """
    Creates and runs the :class:`urwid.MainLoop` object. After the loop exists, it run the :class:`~.ExitAction` from
    the :class:`~.MesonManager`.

    Args:
        top_level_widget: top-level urwid widget for the :class:`urwid.MainLoop` object.
    """
    loop = urwid.MainLoop(top_level_widget, palette=PALETTE, unhandled_input=global_key_handler, handle_mouse=False)
    try:
        loop.run()
    except KeyboardInterrupt:
        urwid.ExitMainLoop()
    meson_manager = MesonManager()
    meson_manager.run_exit_action()
    return 0

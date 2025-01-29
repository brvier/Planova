import re
import os
from functools import partial

from kivy.uix.codeinput import CodeInput  # noqa
from kivy.utils import platform
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.behaviors import (ButtonBehavior, FocusBehavior,
                                ToggleButtonBehavior)
from kivy.uix.label import Label
from kivy.vector import Vector
from kivy.uix.textinput import TextInput
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView

from pygments.lexers.markup import MarkdownLexer

if platform == "android":
    import android

vkeyboard_offset = 0

BLANK_RE = re.compile(r"\s")
URL_RE = re.compile(r"\b((https?|ftp|file)://\S+)")


def get_android_vkeyboard_height():
    print("get_android_vkeyboard_height")
    global vkeyboard_offset
    if platform == "android":
        # for a unknow reason keyboard height can be negative when closed... and
        # an offset persists when open : dirty work arround
        h = android.get_keyboard_height()
        print(h, vkeyboard_offset)
        if not vkeyboard_offset:
            if h < 0:
                vkeyboard_offset = -h
                h = 0
        return h + vkeyboard_offset
    else:
        return Window.keyboard_height


class CircularButton(
    ButtonBehavior,
    Label,
):
    def collide_point(self, x, y):
        return Vector(x, y).distance(self.center) <= self.width / 2


class BottomBar(BoxLayout):
    pass


class MTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # User can change keyboard size during input
        # so we should regularly update the keyboard height
        self.trigger_keyboard_height = Clock.create_trigger(
            self.update_keyboard_height, 0.2, interval=True
        )
        self.trigger_cancel_keyboard_height = Clock.create_trigger(
            lambda dt: self.trigger_keyboard_height.cancel(), 1.0, interval=False
        )

    def update_keyboard_height(self, dt):
        if platform == "android":
            App.get_running_app().keyboard_height = get_android_vkeyboard_height()

    def _bind_keyboard(self):
        super()._bind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height.cancel()
            self.trigger_keyboard_height()

    def _unbind_keyboard(self):
        super()._unbind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height()


class MDInput(CodeInput):

    re_indent_todo = re.compile(r"^\s*(-\s\[\s\]\s)")
    re_indent_done = re.compile(r"^\s*(-\s\[x\]\s)")
    re_indent_list = re.compile(r"^\s*(-\s)")

    def __init__(self, **kwarg):
        CodeInput.__init__(self, lexer=MarkdownLexer(),
                           style_name="gruvbox-dark")
        # User can change keyboard size during input,
        # so we should regularly update the keyboard height
        self.trigger_keyboard_height = Clock.create_trigger(
            self.update_keyboard_height, 0.2, interval=True
        )
        self.trigger_cancel_keyboard_height = Clock.create_trigger(
            lambda dt: self.trigger_keyboard_height.cancel(), 1.0, interval=False
        )

    def update_keyboard_height(self, dt):
        if platform == "android":
            App.get_running_app().keyboard_height = get_android_vkeyboard_height()

    def _bind_keyboard(self):
        super()._bind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height.cancel()
            self.trigger_keyboard_height()

    def _unbind_keyboard(self):
        super()._unbind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height()

    def set_cursor(self, idx):
        self.cursor = self.get_cursor_from_index(idx)
        self.focus = True

    def on_double_tap(self):
        index = self.cursor_index()
        _text = self.text
        if index > 0:
            search_start = 0
            mtch = None
            line_start = _text.rfind("\n", 0, index)

            for mtch in BLANK_RE.finditer(_text[line_start:index]):
                pass
            if mtch:
                search_start = line_start + 1 + mtch.start()

            try:
                search_end = BLANK_RE.search(_text, index).start()
            except AttributeError:
                search_end = len(_text)

            print(_text[search_start:search_end])
            selected_text = _text[search_start:search_end]
            g_url = URL_RE.search(_text, search_start, search_end)

            # Double clic on url
            if g_url:
                print("Found url: ", g_url.groups()[0])
                import webbrowser

                webbrowser.open(g_url.groups()[0])
                return
            # Double clic on link
            if selected_text.startswith("[[") and selected_text.endswith("]]"):
                app = App.get_running_app()
                print("Found internal link: ", selected_text[2:-2])
                pwd = os.path.join(app.getOrgDir(), "notes",
                                   f"{selected_text[2:-2]}.md")
                print(pwd)
                if os.path.exists(pwd):
                    Clock.schedule_once(partial(app.open_note, pwd), 0.2)
                return
            # Else open reorg menu

        super().on_double_tap()

    def do_indent(self, *kwargs):
        index = self.cursor_index()
        if index > 0:
            _text = self.text
            line_start = _text.rfind("\n", 0, index)
            self.text = _text[: line_start + 1] + "  " + _text[line_start + 1:]
            if index > line_start:
                index += 2

        self.set_cursor(index)

    def do_outdent(self, *kwargs):
        index = self.cursor_index()
        _text = self.text
        line_start = _text.rfind("\n", 0, index)
        line_end = _text.find("\n", index)
        if line_end == -1:
            line_end = len(_text)
        if (_text[line_start + 1: line_start + 3]) == "  ":
            self.text = _text[: line_start + 1] + _text[line_start + 3:]
            if index > line_start:
                index -= 2
        self.set_cursor(index)

    def do_heading(self):
        index = self.cursor_index()

        if index >= 0:
            _text = self.text
            line_start = _text.rfind("\n", 0, index)
            line_end = _text.find("\n", index)
            if line_end == -1:
                line_end = len(_text)
            if line_start < 0:
                line_start = -1

            idx = _text.find("# ", line_start + 1, line_end)
            if idx == line_start + 1:
                self.text = "{}{}{}".format(
                    self.text[:idx],
                    "## ",
                    self.text[idx + 2:],
                )
                self.set_cursor(index + (len(self.text) - len(_text)))
                return

            idx = _text.find("## ", line_start + 1, line_end)
            if idx == line_start + 1:
                self.text = "{}{}{}".format(
                    self.text[:idx],
                    "### ",
                    self.text[idx + 3:],
                )
                self.set_cursor(index + (len(self.text) - len(_text)))
                return

            idx = _text.find("### ", line_start + 1, line_end)
            if idx == line_start + 1:
                self.text = "{}{}".format(
                    self.text[:idx],
                    self.text[idx + 4:],
                )
                self.set_cursor(index + (len(self.text) - len(_text)))
                return
            self.text = "{}{}{}".format(
                self.text[: line_start + 1],
                "# ",
                self.text[line_start + 1:],
            )
            self.set_cursor(index + (len(self.text) - len(_text)))
            return

    def do_todo(self):
        index = self.cursor_index()

        if index >= 0:
            _text = self.text
            line_start = _text.rfind("\n", 0, index)
            line_end = _text.find("\n", index)
            if line_end == -1:
                line_end = len(_text)
            if line_start < 0:
                line_start = -1

            idx = _text.find("- [ ]", line_start + 1, line_end)
            if idx >= 0:
                self.text = "{}{}{}".format(
                    self.text[: idx + 3],
                    "x",
                    self.text[idx + 4:],
                )
            else:
                idx = _text.find("- [x]", line_start + 1, line_end)
                if idx >= 0:
                    self.text = "{}{}{}".format(
                        self.text[:idx],
                        "- ",
                        self.text[idx + 6:],
                    )
                else:
                    idx = _text.find("- ", line_start + 1, line_end)
                    if idx >= 0:
                        self.text = "{}{}{}".format(
                            self.text[:idx],
                            "- [ ] ",
                            self.text[idx + 2:],
                        )
                    else:
                        self.text = "{}{}{}".format(
                            self.text[: line_start + 1],
                            "- ",
                            self.text[line_start + 1:],
                        )
            self.set_cursor(index + (len(self.text) - len(_text)))

    def insert_text(self, substring, from_undo=False):
        if not from_undo and self.multiline and self.auto_indent and substring == "\n":
            substring = self._auto_indent(substring)
        CodeInput.insert_text(self, substring, from_undo)

    def _auto_indent(self, substring):
        index = self.cursor_index()

        if index > 0:
            _text = self.text
            line_start = _text.rfind("\n", 0, index)
            if line_start > -1:
                line = _text[line_start + 1: index]  # noqa:E203
                indent = self.re_indent_todo.match(line)

                if indent is None:
                    indent = self.re_indent_done.match(line)
                if indent is None:
                    indent = self.re_indent_list.match(line)
                if indent is not None:
                    substring += indent.group().replace("x", " ")
        return substring


class SelectableRecycleBoxLayout(
    FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout
):
    """Adds selection and focus behaviour to the view."""


# class SelectableNote(RecycleDataViewBehavior, ButtonBehavior, BoxLayout):
#    """Add selection support to the Label"""
#
#    index = None
#    selected = BooleanProperty(False)
#    selectable = BooleanProperty(True)
#    smalltext = StringProperty("")
#    text = StringProperty("")
#    lineno = NumericProperty(0)
#
#    def refresh_view_attrs(self, rv, index, data):
#        """Catch and handle the view changes"""
#        self.index = index
#        return super(SelectableNote, self).refresh_view_attrs(rv, index, data)
#
#    def on_touch_down(self, touch):
#        """Add selection on touch down"""
#        if super(SelectableNote, self).on_touch_down(touch):
#            return True
#        if self.collide_point(*touch.pos) and self.selectable:
#            return self.parent.select_with_touch(self.index, touch)
#
#    def apply_selection(self, rv, index, is_selected):
#        """Respond to the selection of items in the view."""
#
#        self.selected = is_selected
#        if is_selected:
#            rv.data[index].get("text")
#
#
# class SelectableLabel(RecycleDataViewBehavior, ButtonBehavior, Label):
#    """Add selection support to the Label"""
#
#    index = None
#    selected = BooleanProperty(False)
#    selectable = BooleanProperty(True)
#
#    def refresh_view_attrs(self, rv, index, data):
#        """Catch and handle the view changes"""
#        self.index = index
#        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)
#
#    def on_touch_down(self, touch):
#        """Add selection on touch down"""
#        if super(SelectableLabel, self).on_touch_down(touch):
#            return True
#        if self.collide_point(*touch.pos) and self.selectable:
#            return self.parent.select_with_touch(self.index, touch)
#
#    def apply_selection(self, rv, index, is_selected):
#        """Respond to the selection of items in the view."""
#
#        self.selected = is_selected
#        if is_selected:
#            rv.data[index].get("text")


class ToggleLabel(ToggleButtonBehavior, Label):
    active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(ToggleLabel, self).__init__(**kwargs)

        self.allow_no_selection = False
        self.group = "default"


class PlanovaRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super(PlanovaRecycleView, self).__init__(**kwargs)


class PlanovaListItem(RecycleDataViewBehavior, ButtonBehavior, BoxLayout):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    line = StringProperty()
    description = StringProperty()
    when = StringProperty(rebind=True)
    end = StringProperty(rebind=True)
    priority = StringProperty(None)
    path = StringProperty()
    sortkey = None
    # 0 header, 1 todo, 2 event, 3 journal, 4 note
    itemtype = NumericProperty(0)
    filename = StringProperty()
    modified = StringProperty()
    time = StringProperty()
    lineno = NumericProperty(0)

    def __init__(self, **kwargs):
        super(PlanovaListItem, self).__init__(**kwargs)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        return super(PlanovaListItem, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(PlanovaListItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            self.parent.clear_selection()

    def edit(self, idx):
        app = App.get_running_app()
        app.open_note(self.path, self.lineno)

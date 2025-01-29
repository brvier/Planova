import os
import datetime
from functools import partial

from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.app import App
from kivy.clock import Clock

from libs.uix.baseclass.widgets import MDInput
from libs.applibs.models import DailiesData


class DailiesScreen(Screen):
    content = StringProperty()
    calendars = ListProperty()
    dailies = ListProperty()
    todos = ListProperty()
    loading = BooleanProperty(False)

    dailiesData = DailiesData()
    _on_content_timer = None
    _content_filepath = None
    _saved = True

    def on_pre_enter(self, ):
        app = App.get_running_app()
        app.dt = datetime.datetime.now().date()

        self.load_content()
        self.load_model()
        self.load_calendar()
        self.load_dailies()
        self.load_todos()

    def load_model(self):
        app = App.get_running_app()
        pth = os.path.join(app.getOrgDir(), 'dailies')
        self.dailiesData.parse_folder(pth)

    def on_content(self, widget, text):
        if not self.loading:
            self._saved = False
            if self._on_content_timer:
                self._on_content_timer.cancel()
                self._on_content_timer = None
            self._on_content_timer = Clock.schedule_once(partial(self._save, widget, text), 4)

    def _save(self, widget, text, event):
        filepth = self._content_filepath
        if filepth is None:
            return

        print(f"Saving {filepth}")
        with open(filepth, "w") as fh:
            fh.write(self.content)
        self._saved = True
        self.dailiesData.parse_file(filepth)
        self.reload()

    def reload(self):
        self.load_calendar()
        self.load_dailies()
        self.load_todos()

    def load_calendar(self):
        app = App.get_running_app()
        print(app.dt.year, app.dt.month)
        self.calendars = self.dailiesData.get_events_idx_for_month(app.dt.year, app.dt.month)
        print(f"self.calendars={self.calendars}")

    def load_dailies(self):
        app = App.get_running_app()
        self.dailies = self.dailiesData.get_dailies_idx_for_month(app.dt.year, app.dt.month)
        print(f"self.dailies={self.dailies}")

    def load_todos(self):
        app = App.get_running_app()
        self.todos = self.dailiesData.get_todos_idx_for_month(app.dt.year, app.dt.month)
        print(f"self.todos={self.todos}")

    def on_pre_leave(self, ):
        if self._on_content_timer:
            self._on_content_timer.cancel()
            self._on_content_timer = None
        if self._saved is False:
            self._save(self, self.content, None)

    def save(self):
        if self._on_content_timer:
            self._on_content_timer.cancel()
            self._on_content_timer = None
        if self._saved is False:
            self._save(self, self.content, None)

    def on_leave(self):
        self.save()

    def load_content(self):
        if self._on_content_timer:
            self._on_content_timer.cancel()
            self._on_content_timer = None
        if self._saved is False:
            self._save(self, self.content, None)

        app = App.get_running_app()
        filepth = os.path.join(app.getOrgDir(), 'dailies', '{}.md'.format(app.dt.strftime("%Y%m%d")))
        self._content_filepath = filepth
        print(app.dailies.get_events_idx_for_month(app.dt.year, app.dt.month))
        print(f"Try loading {filepth}")
        self.loading = True
        try:
            # Load current daily
            with open(filepth, "r") as fh:
                self.content = fh.read()
        except FileNotFoundError:
            # FIXME Load template
            self.content = """# Events

-

# Todo

- [ ]

# Yacast

- """
        self.loading = False

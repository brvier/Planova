import os
import humanize
import datetime

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import (
    DictProperty,
    ListProperty
)
from kivy.uix.recycleview import RecycleView


class Item:
    description = None
    path = None
    itemtype = 0
    lineno = 0

    def __init__(self, description, path, lineno):
        self.description = description
        self.path = path
        self.itemtype = 0
        self.lineno = lineno

    def toDict(self):
        return {
            "description": self.description,
            "itemtype": 0,
        }


class Note(Item):
    category = None
    modified = None

    def __init__(self, description, path):
        super(Note, self).__init__(description, path, lineno=None)
        self.modified = os.path.getmtime(path)
        self.category = os.path.dirname(path)

    def toDict(self):
        return {
            "description": self.description,
            "modified": humanize.naturaltime(
                datetime.datetime.fromtimestamp(self.modified)
            ),
            "category": self.category,

            "path": self.path,
            "lineno": 0,
            "itemtype": 4,
        }


class PlanovaNotesRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super(PlanovaNotesRecycleView, self).__init__(**kwargs)


class NotesScreen(Screen):
    notes = ListProperty([])

    def on_pre_enter(self, ):
        self._load()

    def _load(self):
        app = App.get_running_app()
        n = {}
        for path, dirs, files in os.walk(os.path.join(app.getOrgDir(), "notes")):
            dirs = [d for d in dirs if not d.startswith(".")]
            files = [f for f in files if not f.startswith(".")]
            if any([prt.startswith(".") for prt in path.split("/")]):
                continue

            for file in files:
                k = os.path.dirname(os.path.relpath(os.path.join(
                    path, file), os.path.join(app.getOrgDir(), "notes")))

                if file.startswith(".") or os.path.basename(path).startswith("."):
                    continue
                if file.endswith(".txt") or file.endswith(".md"):
                    try:
                        n[k].append(
                            Note(
                                description=file,
                                path=os.path.join(path, file),
                            ).toDict()
                        )
                    except Exception:
                        n[k] = [
                            Note(
                                description=file,
                                path=os.path.join(path, file),
                            ).toDict()]

        self.notes.clear()
        try:
            for k in sorted(n.keys()):
                self.notes.append(
                    Item(
                        description=k if k else 'Notes',
                        path=None,
                        lineno=None,
                    ).toDict()
                )
                for nn in n[k]:
                    print(type(nn), k, nn)
                for nn in sorted(n[k], key=lambda x: x['modified'], reverse=True):
                    self.notes.append(nn)
        except KeyError:
            pass

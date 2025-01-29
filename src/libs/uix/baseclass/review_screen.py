import os
import datetime

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import (
    DictProperty,
    ListProperty
)
from libs.applibs.models import DailiesData


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


class Todo(Item):
    def __init__(self, status, description, path, lineno, dt):
        super(Todo, self).__init__(description, path, lineno=lineno)
        self.dt = dt
        self.status = status

    def toDict(self):
        return {
            "status": self.status,
            "description": self.description,
            "path": self.path,
            "lineno": self.lineno,
            "itemtype": 1,
            "dt": self.dt,
            "time": datetime.datetime.fromtimestamp(
                self.dt).strftime("%a %d %b %y")
        }

class Event(Item):
    def __init__(self, description, path, lineno, dt):
        super(Event, self).__init__(description, path, lineno=lineno)
        self.dt = dt

    def toDict(self):
        return {
            "description": self.description,
            "path": self.path,
            "lineno": self.lineno,
            "itemtype": 2,
            "dt": self.dt,
            "time": datetime.datetime.fromtimestamp(
                self.dt).strftime("%a %d %b %y")
        }



class ReviewScreen(Screen):
    items = ListProperty([])

    def on_pre_enter(self):
        self._load()

    def _load(self):
        app = App.get_running_app()

        self.items.clear()
        for t in app.dailies.get_todos():
            self.items.append(Todo(
                status=t[0],
                description=t[1],
                path=t[2],
                lineno=t[3],
                dt=t[4]).toDict())

        for e in app.dailies.get_future_events(datetime.datetime.now()):
                self.items.append(Event(
                    description=e[0],
                    path=e[1],
                    lineno=e[2],
                    dt=e[3]).toDict())


        # Sort by dt
        self.items.sort(key=lambda t: t['dt'])

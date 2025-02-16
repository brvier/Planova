__author__ = "Benoît HERVIER"
__copyright__ = "Copyright 2022, Benoît HERVIER"
__license__ = "MIT"
__version__ = "0.6.2"
__email__ = "b@rvier.fr"
__status__ = "Developpment"

import datetime
import os
import re
from dateutil.relativedelta import relativedelta
from functools import partial

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import ObjectProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase

from libs.applibs.models import DailiesData
from libs.uix.root import Root
from libs.uix.baseclass.themes import Theme

Window.softinput_mode = ''

ORG_PATH = os.path.expanduser("~/Org")
if platform == "android":
    from android import mActivity
    context = mActivity.getApplicationContext()
    ORG_PATH = context.getExternalMediaDirs()[0].getPath()


class MainApp(App):
    dt = ObjectProperty(datetime.datetime.now().date(), rebind=True)
    dailies = ObjectProperty(DailiesData(), rebind=True)
    theme = ObjectProperty(Theme(), rebind=True)

    keyboard_height = NumericProperty(0)

    def getOrgDir(self):
        return ORG_PATH

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title = "Planova"
        Window.keyboard_anim_args = {"d": 0.1, "t": "linear"}
        Window.softinput_mode = ""
        Clock.schedule_once(self.__init_later__, 0.1)

    def __init_later__(self, dt):
        if not os.path.exists(os.path.join(ORG_PATH, "dailies")):
            os.makedirs(os.path.join(ORG_PATH, "dailies"))
        if not os.path.exists(os.path.join(ORG_PATH, "notes")):
            os.makedirs(os.path.join(ORG_PATH, "notes"))
        self.dailies.parse_folder(os.path.join(ORG_PATH,
                                               "dailies"))

    def on_stop(self):
        try:
            self.root.children[0].on_leave()
        except Exception:
            pass

    def build(self):
        self.root = Root()
        self.root.sm.push("dailies")

    def on_day(self, d):
        self.dt = self.dt.replace(day=int(d))
        self.root.sm.children[0].save()
        self.root.sm.children[0].reload()
        self.root.sm.children[0].load_content()

    def on_month(self, d):
        self.dt = self.dt + relativedelta(months=int(d))
        self.root.sm.children[0].save()
        self.root.sm.children[0].reload()
        self.root.sm.children[0].load_content()

    def on_today(self):
        self.dt = datetime.datetime.now().date()
        self.root.sm.children[0].save()
        self.root.sm.children[0].reload()
        self.root.sm.children[0].load_content()

    def open_note(self, path, lineno=0):
        if os.path.dirname(path).endswith('dailies'):
            print('open_daily', path, lineno)
            daily_pattern = r'(\d{4}\d{2}\d{2}).md'
            filename = os.path.basename(path)
            daily_match = re.match(daily_pattern, filename)
            if daily_match:
                print('matching daily pattern')
                self.root.sm.push("dailies")
                self.dt = datetime.datetime.strptime(
                    daily_match.group(1), '%Y%m%d')
                Clock.schedule_once(partial(self._edit_daily, self.dt), 0)
                return

        print('open_note', path, lineno)

        self.root.sm.push("note")
        Clock.schedule_once(partial(self._edit_note, path, lineno), 0)

    def _edit_note(self, path, lineno, event):
        print(self.root.sm.children[0], type(path))
        self.root.sm.children[0].path = path
        self.root.sm.children[0].load_note()


    def _edit_daily(self, dt,  event):
        self.dt = dt
        self.root.sm.children[0].reload()
        self.root.sm.children[0].load_content()
 

if __name__ == "__main__":
    LabelBase.register(
        name="awesome", fn_regular="data/fonts/fa-solid-900.ttf"
    )
    MainApp().run()

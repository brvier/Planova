import logging
from functools import partial

from kivy.uix.screenmanager import Screen
from kivy.properties import (
    StringProperty,
    BooleanProperty
)
from kivy.clock import Clock

logger = logging.getLogger("Planova.note_screen")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class NoteScreen(Screen):

    content = StringProperty('')
    path = StringProperty('')
    loading = BooleanProperty(False)

    _on_content_timer = None
    _saved = True

    def on_content(self, widget, text):
        logger.debug("on_content")
        if not self.loading:
            self._saved = False
            if self._on_content_timer:
                self._on_content_timer.cancel()
                self._on_content_timer = None
            self._on_content_timer = Clock.schedule_once(self._save, 4)

    def on_pre_leave(self, ):
        if self._on_content_timer:
            self._on_content_timer.cancel()
            self._on_content_timer = None
        if self._saved is False:
            self._save(self)

    def save(self):
        if self._on_content_timer:
            self._on_content_timer.cancel()
            self._on_content_timer = None
        if self._saved is False:
            self._save(self)

    def on_leave(self):
        self.save()

    def load_note(self):
        ''' load note from path '''
        self.loading = True
        try:
            with open(self.path, 'r') as f:
                self.content = f.read()
        except Exception as err:
            logger.exception(err)
        self.loading = False

    def _save(self, dt=None):
        logger.debug("_save")
        if not self.path:
            logger.error("No path defined")
            return
        try:
            with open(self.path, 'w') as f:
                f.write(self.content)
            self._saved = True
        except Exception as err:
            logger.exception(err)


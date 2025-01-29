from kivy.event import EventDispatcher


from kivy.properties import (
    StringProperty,
    NumericProperty,
    ListProperty,
    ColorProperty,
)


class Theme(EventDispatcher):
    BackgroundColor = ColorProperty("#282828ff")
    BackgroundRGBA = ListProperty((.157, .157, .157, 1))
    BackgroundRGBADarker = ListProperty((.157, .157, .157, .8))
    HeaderBackgroundColor = ColorProperty("#191919ff")
    PrimaryColor = ColorProperty("#ffffffff")
    AccentColor = ColorProperty("ff0000ff")
    AccentBackgroundColor = ColorProperty("333333ff")
    AccentBackgroundRGBA = ListProperty((.2, .2, .2, 1))
    SecondAccentColor = ColorProperty("#d65d0eff")
    SecondAccentBackgroundColor = ColorProperty("1c92ecff")
    TodoColor = ColorProperty("#d65d0eff")
    EventColor = ColorProperty("#d79921ff")
    NoteColor = ColorProperty("#7c6f64ff")
    DailyColor = ColorProperty("#689d6aff")

    def __init__(self, **kwargs):
        super(Theme, self).__init__(**kwargs)

    def set_light(self):
        pass

    def set_dark(self):
        pass


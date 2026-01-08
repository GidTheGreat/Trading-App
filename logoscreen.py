from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle


class LogoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg, pos=self._update_bg)

        self.logo = Image(
    source="novablazar.png",
    size_hint=(1, 1),
    pos_hint={"center_x": 0.5, "center_y": 0.5},
    allow_stretch=True,
    keep_ratio=False,
    opacity=1,
)
        self.add_widget(self.logo)

        Clock.schedule_once(self.fade_out_logo, 5)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def fade_out_logo(self, dt):
        anim = Animation(opacity=0, duration=1)
        anim.bind(on_complete=self.on_fade_complete)
        anim.start(self.logo)

    def on_fade_complete(self, *args):
        # Switch to main screen (StarField)
        self.manager.current = "setup"
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import NumericProperty


class MarqueeLabel(Label):
    scroll_x = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_size = (None, None)
        self.size_hint = (None, None)
        self.bind(texture_size=self.update_size)
        Clock.schedule_once(self._init_position, 0)

    def update_size(self, *args):
        self.size = self.texture_size

    def _init_position(self, dt):
        if not self.parent:
            return
        self.x = self.parent.width  # Start just off-screen on the right
        self.center_y = self.parent.center_y  # Vertically center
        Clock.schedule_interval(self.scroll_text, 1 / 60)

    def scroll_text(self, dt):
        self.x -= 1  # Adjust scroll speed here
        if self.right < 0:
            self.x = self.parent.width  # Restart from the right edge

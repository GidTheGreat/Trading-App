from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.clock import Clock
from collections import deque
import time
from kivy.core.text import Label as CoreLabel
from datetime import datetime
from kivy.graphics import Line, Color, Rectangle
from kivy.uix.widget import Widget



class GraphWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ticks = deque(maxlen=300)
        self.bind(size=self.redraw, pos=self.redraw)
        Clock.schedule_interval(self.redraw, 1 / 30)

    def set_data(self, ticks):
        self.ticks = ticks

    def redraw(self, *args):
        if not self.ticks or len(self.ticks) < 2:
            return

        self.canvas.clear()
        with self.canvas:
            Color(0.94, 0.94, 0.94)  # soft grey-white line  # Green line
            points = []

            times, prices = zip(*self.ticks)
            min_time, max_time = min(times), max(times)
            min_price, max_price = min(prices), max(prices)

            time_span = max(max_time - min_time, 1e-5)
            price_span = max(max_price - min_price, 1e-5)

            for t, p in self.ticks:
                x = self.x + (t - min_time) / time_span * self.width
                y = self.y + (p - min_price) / price_span * self.height
                points += [x, y]

            Line(points=points, width=1.2)

            # === Labels ===
            Color(1, 1, 1, 1)
            label_count = min(4, len(self.ticks))
            if label_count > 1:
                step = len(self.ticks) // (label_count - 1)

                for i in range(0, len(self.ticks), step):
                    t, p = self.ticks[i]

                    # Y label
                    y = self.y + (p - min_price) / price_span * self.height
                    y_label = CoreLabel(text=f"{p:.2f}", font_size=12)
                    y_label.refresh()
                    if y_label.texture:
                        Rectangle(
                            texture=y_label.texture,
                            size=y_label.texture.size,
                            pos=(self.x + 5, y)
                        )

                    # X label
                    # X label (converted from UNIX timestamp)
                    
                    x = self.x + (t - min_time) / time_span * self.width
                    readable_time = datetime.fromtimestamp(t).strftime("%H:%M:%S")
                    x_label = CoreLabel(text=readable_time, font_size=12)
                    x_label.refresh()
                    if x_label.texture:
                        Rectangle(
                            texture=x_label.texture,
                            size=x_label.texture.size,
                            pos=(x, self.y + 5)
                        )

            

class TickChart(FloatLayout):
    def __init__(self, container=None, max_points=300, **kwargs):
        super().__init__(**kwargs)
        self.max_points = max_points
        self.ticks_by_symbol = {}
        self.current_symbol = None
        self.container = container

        if container:
            self.size_hint = (None, None)
            self.size = container.size
            self.pos = container.pos
            container.bind(size=self._update_size, pos=self._update_pos)

        self.graph = GraphWidget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.graph)

        self.quote_label = Label(
            text="Quote: --",
            font_size=16,
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(dp(160), dp(30)),
            pos_hint={'center_x': 0.5, 'y': 0.35}
        )
        self.add_widget(self.quote_label)

        Clock.schedule_interval(self.graph.redraw, 1 / 30)

    def _update_size(self, *_):
        self.size = self.container.size

    def _update_pos(self, *_):
        self.pos = self.container.pos

    def set_symbol(self, symbol):
        self.current_symbol = symbol
        ticks = self.ticks_by_symbol.get(symbol, deque())
        self.graph.set_data(ticks)

    def add_tick(self, symbol, quote, timestamp=None):
        timestamp = timestamp or time.time()
        if symbol not in self.ticks_by_symbol:
            self.ticks_by_symbol[symbol] = deque(maxlen=self.max_points)
        self.ticks_by_symbol[symbol].append((timestamp, quote))
        if symbol == self.current_symbol:
            self.graph.set_data(self.ticks_by_symbol[symbol])
            self.quote_label.text = f"Quote: {quote:.5f}"

    def set_timeframe(self, tf):
        pass  # Intentionally empty

from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.graphics import Line, Color, Rectangle
from kivy.metrics import dp
#from ui_logger import kivy_print
from kivy.core.text import Label as CoreLabel

class CandleChart(FloatLayout):
    def __init__(self, container=None, **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.completed_candles = {}  # (symbol, timeframe): [candles]
        self.forming_candle = {}     # (symbol, timeframe): candle dict
        self.current_symbol = None
        self.current_timeframe = None

        if container:
            self.size_hint = (None, None)
            self.size = container.size
            self.pos = container.pos
            container.bind(size=self._update_size, pos=self._update_pos)

        Clock.schedule_interval(self.redraw, 1 / 30)

    def _update_size(self, *_):
        self.size = self.container.size

    def _update_pos(self, *_):
        self.pos = self.container.pos

    def set_symbol(self, symbol):
        self.current_symbol = symbol

    def set_timeframe(self, timeframe):
        self.current_timeframe = timeframe

    def add_candle(self, symbol, timeframe, candle):
        key = (symbol, timeframe)
        if key not in self.completed_candles:
            self.completed_candles[key] = []
        self.completed_candles[key].append(candle)
        if len(self.completed_candles[key]) > 100:
            self.completed_candles[key].pop(0)

    def update_forming_candle(self, symbol, timeframe, candle):
        key = (symbol, timeframe)
        self.forming_candle[key] = candle
        
    def redraw(self, dt):
        self.canvas.clear()
        key = (self.current_symbol, self.current_timeframe)
        candles = self.completed_candles.get(key, [])
        forming = self.forming_candle.get(key)

        with self.canvas:
            # === Outline ===
            #Color(0, 1, 0, 0.4)
            #Line(rectangle=(self.x, self.y, self.width, self.height), width=1.5)

            # === Debug Text ===
            Color(1, 1, 1, 1)
            info_lines = [
                f"Symbol: {self.current_symbol or '--'}",
                f"Timeframe: {self.current_timeframe or '--'}",
                f"Completed Candles: {len(candles)}"
            ]

            if forming:
                color = "GREEN" if forming["close"] >= forming["open"] else "RED"
                info_lines.append(f"Forming Candle: {color}")
            else:
                info_lines.append("Forming Candle: None")

            for idx, line in enumerate(info_lines):
                label = CoreLabel(text=line, font_size=14)
                label.refresh()
                if label.texture:
                    Rectangle(
                        texture=label.texture,
                        size=label.texture.size,
                        pos=(self.x + 10, self.top - 20 - idx * 22)
                    )

            # === Candle Plotting ===
            if not candles:
                return

            # Plot settings
            padding_x = dp(10)
            padding_y = dp(10)
            plot_x = self.x + padding_x
            plot_y = self.y + padding_y
            plot_w = self.width - 2 * padding_x
            plot_h = self.height - 2 * padding_y

            # Candle data to draw
            all_candles = candles[-50:]  # Limit to last 50
            if forming:
                all_candles = all_candles + [forming]

            highs = [c["high"] for c in all_candles]
            lows = [c["low"] for c in all_candles]
            min_price = min(lows)
            max_price = max(highs)
            price_range = max(max_price - min_price, 1e-5)

            count = len(all_candles)
            spacing = plot_w / count
            candle_width = spacing * 0.6

            def norm_y(price):
                return plot_y + ((price - min_price) / price_range) * plot_h

            for idx, candle in enumerate(all_candles):
                o, h, l, c = candle["open"], candle["high"], candle["low"], candle["close"]

                x = plot_x + idx * spacing
                body_y = norm_y(min(o, c))
                body_h = abs(norm_y(o) - norm_y(c))
                wick_y1 = norm_y(l)
                wick_y2 = norm_y(h)

                # Color
                Color(0, 1, 0, 1) if c >= o else Color(1, 0, 0, 1)

                # Wick
                Line(points=[
                    x + candle_width / 2, wick_y1,
                    x + candle_width / 2, wick_y2
                ], width=1.2)

                # Body
                Rectangle(pos=(x, body_y), size=(candle_width, max(1, body_h)))

    """
    def redraw(self, dt):
        self.canvas.clear()
        key = (self.current_symbol, self.current_timeframe)
        candles = self.completed_candles.get(key, [])
        forming = self.forming_candle.get(key)
        #print(f"[REDRAW] Candles found for {self.current_symbol} {self.current_timeframe}: {len(candles)}")

        

        with self.canvas:
            # Draw chart area outline
            Color(0, 1, 0, 0.4)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1.5)

            # === Text debug overlay ===
            Color(1, 1, 1, 1)

            info_lines = [
                f"Symbol: {self.current_symbol or '--'}",
                f"Timeframe: {self.current_timeframe or '--'}",
                f"Completed Candles: {len(candles)}",
            ]

            if forming:
                color = "GREEN" if forming["close"] >= forming["open"] else "RED"
                info_lines.append(f"Forming Candle: {color}")
            else:
                info_lines.append("Forming Candle: None")

            # Draw lines top-down
            for idx, line in enumerate(info_lines):
                label = CoreLabel(text=line, font_size=14)
                label.refresh()
                if label.texture:
                    Rectangle(
                        texture=label.texture,
                        size=label.texture.size,
                        pos=(self.x + 10, self.top - 20 - idx * 22)
                    )
            """

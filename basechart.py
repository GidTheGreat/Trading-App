from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from tickchart import TickChart
from candlechart import CandleChart
#from ui_logger import kivy_print

class BaseChart(FloatLayout):
    def __init__(self, container=None, **kwargs):
        super().__init__(**kwargs)
        self.container = container
        self.current_symbol = None
        self.current_timeframe = "tick"
        self.available_candle_data = {}  # {symbol: set([timeframes])}

        if container:
            self.size_hint = (None, None)
            self.size = container.size
            self.pos = container.pos
            container.bind(size=self._update_size, pos=self._update_pos)

        # Pass container to children for layout consistency
        self.tick_chart = TickChart(container=self)
        self.candle_chart = CandleChart(container=self)

        self.active_chart = self.tick_chart
        self.add_widget(self.active_chart)

    def _update_size(self, *_):
        self.size = self.container.size

    def _update_pos(self, *_):
        self.pos = self.container.pos


    def _switch_chart(self, chart_widget):
        if self.active_chart and self.active_chart.parent:
            self.remove_widget(self.active_chart)
        self.active_chart = chart_widget
        self.add_widget(self.active_chart)

    def set_symbol(self, symbol):
        self.current_symbol = symbol
        self.tick_chart.set_symbol(symbol)
        self.candle_chart.set_symbol(symbol)
        self.refresh_chart()

    def set_timeframe(self, timeframe):
        self.current_timeframe = timeframe
        self.refresh_chart()

    def refresh_chart(self):
        if self.current_timeframe == "tick":
            self._switch_chart(self.tick_chart)
        else:
            self._switch_chart(self.candle_chart)
        self.active_chart.set_symbol(self.current_symbol)
        if hasattr(self.active_chart, "set_timeframe"):
            self.active_chart.set_timeframe(self.current_timeframe)

    def add_tick(self, symbol, quote, timestamp=None):
        self.tick_chart.add_tick(symbol, quote, timestamp)

    def add_candle(self, symbol, timeframe, candle):
        #print(candle)
        # Track available data
        if symbol not in self.available_candle_data:
            self.available_candle_data[symbol] = set()
        self.available_candle_data[symbol].add(timeframe)

        # Only add if relevant
        if symbol == self.current_symbol and timeframe == self.current_timeframe:
            self.candle_chart.add_candle(symbol, timeframe, candle)


    def update_forming_candle(self, symbol, timeframe, candle):
        if symbol == self.current_symbol and timeframe == self.current_timeframe:
            self.candle_chart.update_forming_candle(symbol, timeframe, candle)

    def refresh_chart(self):
        if self.current_timeframe == "tick":
            self._switch_chart(self.tick_chart)
            self.active_chart.set_symbol(self.current_symbol)
        else:
            symbol = self.current_symbol
            tf = self.current_timeframe

            if symbol in self.available_candle_data and tf in self.available_candle_data[symbol]:
                self._switch_chart(self.candle_chart)
                self.active_chart.set_symbol(symbol)
                self.active_chart.set_timeframe(tf)
            else:
                print(f"[SKIP] No candle data for {symbol} / {tf}")
                self._switch_chart(Widget())



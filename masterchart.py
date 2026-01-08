from kivy.uix.floatlayout import FloatLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivymd.uix.button import MDRaisedButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from collections import deque
import time
from kivy.graphics import Line, Color, Rectangle, Triangle
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from botutils.event_loop import loop, stop_event
from bot_runner import BotRunner
from threading import Thread
import asyncio
from botutils.async_scheduler import schedule_coroutine
from basechart import BaseChart
from botutils import runtimeglobals

class MasterChart(FloatLayout):
    def __init__(self, container, **kwargs):
        super().__init__(**kwargs)
        self.container = container

        self.symbols = []  # Fill from your data source
        self.timeframes = ["tick","1min","5min","15min","30min","1hr","4hr"]
        print(self.timeframes)
        self.indicators = ["Bollinger", "RSI"]
        self.current_symbol = ""
        self.current_timeframe = "tick"

        # === Bind MasterChart to container ===
        self.size_hint = (None, None)
        self.size = container.size
        self.pos = container.pos
        container.bind(size=self._update_size, pos=self._update_pos)

        # === CHART AREA ===
        self.canvas_area = FloatLayout(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.canvas_area)
        
        #Clock.schedule_once(self.draw_borders, 0)
        # Redraw on resize or move
        #self.bind(size=self.draw_borders, pos=self.draw_borders)

        # === Chart Widgets ===
        self.base_chart = BaseChart(container=self.canvas_area)
        self.canvas_area.add_widget(self.base_chart)

        # === Dropdowns ===
        self.symbol_dropdown, self.symbol_layout = self._create_dropdown(self.symbols, self.set_symbol)
        self.symbol_button = self._create_dropdown_button("Select Symbol", self.symbol_dropdown, {'right': 0.98, 'top': 1})

        self.timeframe_dropdown, _ = self._create_dropdown(self.timeframes, self.set_timeframe)
        self.timeframe_button = self._create_dropdown_button("Tick", self.timeframe_dropdown, {'right': 0.75, 'top': 1})
        self.indicator_dropdown, _ = self._create_dropdown(self.indicators, self.add_indicator)
        self.indicator_button = self._create_dropdown_button("Indicators", self.indicator_dropdown, {'right': 0.52, 'top': 1})

        self.canvas_area.add_widget(self.symbol_button)
        self.canvas_area.add_widget(self.timeframe_button)
        self.canvas_area.add_widget(self.indicator_button)
        self.bot_runner = BotRunner(loop,stop_event)
        

        # === Start/Stop Analysis Button ===
        
        self.analysis_thread = None
        self.analysis_running = False 
        runtimeglobals.analysis_running = False
        self.analysis_button = Button(
                text="Start Analysis",
                size_hint=(None, None),
                size=(dp(140), dp(40)),
                pos_hint={"right": 1, "y": 0},
                background_color=(0.2, 0.6, 0.2, 1),
                font_size='15sp'
            )
        
        
        self.analysis_button.bind(on_release=self.toggle_analysis)
        
        self.canvas_area.add_widget(self.analysis_button)
        
        self.set_timeframe("tick")

    
    
        
    # === Helpers ===
    def toggle_analysis(self, instance):
        if self.analysis_running:
            self.bot_runner.stop_event.set()  
            self.analysis_button.text = "▶ Start Analysis"
            self.analysis_button.opacity = 1
            self.analysis_running = False
            runtimeglobals.analysis_running = False
            
        else:
                self.bot_runner.stop_event.clear()
                self.analysis_thread = Thread(target=self.bot_runner.run, daemon=True)
                self.analysis_thread.start()
                self.analysis_button.text = "⏹ Stop Analysis"
                self.analysis_button.opacity = 0.02
                self.analysis_running = True
                runtimeglobals.analysis_running = True
                
            
  
    def place_trade_up(self, instance):
        from botutils.place_trade import place_trade
        schedule_coroutine(place_trade,self.current_symbol,"CALL", label="Place Trade Up")
        print("➡️ Place Trade Up requested")
        
    def place_trade_down(self, instance):
        from botutils.place_trade import place_trade
        schedule_coroutine(place_trade,self.current_symbol,"PUT", label="Place Trade Down")
        print("➡️ Place Trade Down requested")
        
    def draw_borders(self, *args):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(0, 1, 0, 1)  # Bright green
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2)

    def _update_size(self, instance, size):
        self.size = size

    def _update_pos(self, instance, pos):
        self.pos = pos

    def _create_dropdown(self, items, on_select_callback, max_visible_items=4):
        item_height = dp(32)
        item_spacing = dp(4)
        dropdown_height = max_visible_items * item_height + (max_visible_items - 1) * item_spacing
    
        dropdown = DropDown(auto_width=False, width=dp(140), max_height=dropdown_height)
        dropdown.background_color = (0, 0, 0, 0)
    
        scroll = ScrollView(size_hint=(None, None), size=(dp(140), dropdown_height))
        layout = GridLayout(cols=1, size_hint_y=None, spacing=item_spacing)
        layout.bind(minimum_height=layout.setter('height'))
    
        def create_button(item_text):
            btn = Button(
                text=item_text,
                size_hint_y=None,
                height=item_height,
                background_normal='',
                background_color=(0, 0, 0, 0.2),
                color=(1, 1, 1, 1),
                font_size='15sp'
            )
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            return btn
    
        for item in items:
            layout.add_widget(create_button(item))
    
        scroll.add_widget(layout)
        dropdown.add_widget(scroll)
        dropdown.bind(on_select=lambda _, val: on_select_callback(val))
    
        return dropdown, layout

    def _create_dropdown_button(self, text, dropdown, pos_hint):
        btn = Button(
            text=text,
            size_hint=(None, None),
            size=(dp(120), dp(40)),
            pos_hint=pos_hint,
            background_normal='',
            background_color=(0, 0, 0, 0.3),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        btn.bind(on_release=lambda _: self._open_dropdown(dropdown, btn))
        return btn

    def _open_dropdown(self, dropdown, button):
        dropdown.opacity = 0
        dropdown.open(button)
        Animation(opacity=1, duration=0.2).start(dropdown)

    # === Logic ===
    def _add_symbol_to_dropdown(self, symbol):
        btn = Button(
            text=symbol,
            size_hint_y=None,
            height=dp(32),
            background_normal='',
            background_color=(0, 0, 0, 0.2),
            color=(1, 1, 1, 1),
            font_size='15sp'
        )
        btn.bind(on_release=lambda btn: self.symbol_dropdown.select(btn.text))
        self.symbol_layout.add_widget(btn)
        
        
    def set_symbol(self, symbol):
        if not symbol:
            return
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self._add_symbol_to_dropdown(symbol)

        self.current_symbol = symbol
        self.symbol_button.text = symbol
        self.base_chart.set_symbol(symbol)

    def set_timeframe(self, timeframe):
        self.current_timeframe = timeframe
        self.timeframe_button.text = timeframe
        self.base_chart.set_timeframe(timeframe)


    def add_indicator(self, name):
        self.indicator_button.text = name
        pass
        #if hasattr(self.chart, "add_indicator"):
            #self.chart.add_indicator(name)

    def add_tick(self, symbol, quote, timestamp=None):
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self._add_symbol_to_dropdown(symbol)
        if not self.current_symbol:
            self.set_symbol(symbol)
        self.base_chart.add_tick(symbol, quote, timestamp)

    def add_candle_data(self, category, key, message):
        if category != "candles":
            return

        if key.startswith("candles_") or key.startswith("forming_"):
            prefix = "candles_" if key.startswith("candles_") else "forming_"
            key_body = key[len(prefix):]  # Remove 'candles_' or 'forming_'
            try:
                symbol, tf = key_body.rsplit("_", 1)
            except ValueError:
                return  # Invalid format

            if key.startswith("candles_"):
                for candle in message:
                    #print(f"[DEBUG] Adding completed candle data: {symbol} {tf} {candle}")
                    self.base_chart.add_candle(symbol, tf, candle)
            else:
                #print(f"[DEBUG] Adding forming candle data: {symbol} {tf}")
                self.base_chart.update_forming_candle(symbol, tf, message)



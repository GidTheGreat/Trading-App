from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from startbot_options.labeled_textfield import LabeledTextInput
from kivy.uix.screenmanager import ScreenManager
from botutils import runtimeglobals
import json
import os
from collections import deque
from kivy.app import App
from kivy.utils import get_color_from_hex
from startbot_options.checkbox_dropdown_field import CheckboxDropdown

from startbot_options.nestedfield import Nested
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.clock import Clock




class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = get_color_from_hex("#000000")
        
        scroll_view = ScrollView()
        content = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        
        self.mode = CheckboxDropdown(label="Run Mode", options=["Local", "Server"],default_selected=["Local"],
    multiselect=False,
    preview_selected=True,
    special=True)
        content.add_widget(self.mode)
        
        self.server_url= LabeledTextInput(label = "Server Url",default = "20.245.150.45:5000",hidden = True)
        content.add_widget(self.server_url)

        self.secret_code= LabeledTextInput(label = "Secret Code",default = "my_secret_code", special = True,hidden = True)
        content.add_widget(self.secret_code)

        self.API_token= LabeledTextInput(label = "API TOKEN",default = "wPYKJXzoLKJYBVU",hidden = True)
        content.add_widget(self.API_token)
        
        self.app_id= LabeledTextInput(label = "App ID",default = "82751",input_type = int,special = True,hidden = True)
        content.add_widget(self.app_id)
        
        self.symbols_dropdown = CheckboxDropdown(label="Symbols", options=["R_25", "R_50", "R_75", "R_100"],default_selected=["R_25"],
    multiselect=True,
    preview_selected=True)
        content.add_widget(self.symbols_dropdown)
        
        self.trade_type_dropdown = CheckboxDropdown(label="trade type", options=["higher/lower", "rise/fall", "multipliers"],default_selected=["higher/lower"],
    multiselect=False,
    preview_selected=True)
        content.add_widget(self.trade_type_dropdown)
        
        self.martingale_type = CheckboxDropdown(label="martingale type", options=["mode_x2", "mode_x23factor", "mode_3factor"],default_selected=["mode_x2"],
    multiselect=False,
    preview_selected=True)
        content.add_widget(self.martingale_type)
        
        self.stake = LabeledTextInput(label = "Stake", input_type = float, min_value = 0.35,max_value = 1000, default = "0.35")
        content.add_widget(self.stake)
        
        self.martingale_multiplier = LabeledTextInput(label = "martingale multiplier", input_type = int, min_value = 1,max_value = 8, default = "2")
        content.add_widget(self.martingale_multiplier)
        
        self.trade_duration = Nested(
    parent_config={
        "label": "Choose trade timeframe",
        "options": ["ticks", "mins"],
        "default_selected":["ticks"],
        "multiselect": False
    },
    children_config_map={
        "ticks": [{
        "type": "textinput",
        "kwargs": {
            "label": "trade duration",
            "input_type":int,
            "min_value": 1,
            "max_value":60,
            "default" :"5",
        }
    }],
        
        "mins": [
    {
        "type": "textinput",
        "kwargs": {
            "label": "trade duration",
            "input_type":int,
            "min_value": 1,
            "max_value":60,
            "default" :"1",
        }
    }
],
        
     }  
)

        content.add_widget(self.trade_duration)
        
        self.strategy = Nested(
    parent_config={
        "label": "Choose strategy",
        "options": ["candle_color", "bollinger","macdmomentum","macdcrossover","macdhistogram"],
        "default_selected":["candle_color","macdhistogram"]
    },
    children_config_map={
         "macdmomentum": [{
        "type": "checkbox",
        "kwargs": {
            "label": "macdmomentum_timeframe",
            "options": ["tick","1min","5min","15min","30min","1hr","4hr"],
            "default_selected": ["1min"]
        }
    }],
        "macdcrossover": [{
        "type": "checkbox",
        "kwargs": {
            "label": "macdcrossover_timeframe",
            "options": ["tick","1min","5min","15min","30min","1hr","4hr"],
            "default_selected": ["tick"]
        }
    }],
        "macdhistogram": [{
        "type": "checkbox",
        "kwargs": {
            "label": "macdhistogram_timeframe",
            "options": ["tick","1min","5min","15min","30min","1hr","4hr"],
            "default_selected": ["1min", "5min"]
        }
    }],
        
        "candle_color": [
    {
        "type": "checkbox",
        "kwargs": {
            "label": "candle_color_timeframe",
            "options": ["1min","5min","15min","30min","1hr","4hr"],
            "default_selected": ["1min","5min"]
        }
    }
],
        
        "bollinger": [
        {
            "type": "checkbox",
            "kwargs": {
                "label": "bollinger_timeframe",
                "options": ["tick", "1min", "5min", "15min"],
                "default_selected": ["tick"]
            }
        }
    ]
}
)

        content.add_widget(self.strategy)
        # Submit Button
        submit_btn = Button(text="Save&Continue",
        background_color=(0.2, 0.6, 0.2, 1),
         on_release=self.on_setup_complete, size_hint_y=None, height=dp(50))
        content.add_widget(submit_btn)
        
        scroll_view.add_widget(content)
        self.add_widget(scroll_view)

    def extract_strategy_combinations(self,strategy_dict):
        strategies = []
        all_timeframes = set()
    
        for parent in strategy_dict.get("parent", []):
            key = f"{parent}_timeframe"
            timeframes = strategy_dict.get("children", {}).get(key, [])
    
            for tf in timeframes:
                strategies.append(f"{parent}_{tf}")
                all_timeframes.add(tf)
    
        return strategies, all_timeframes
    
    def print_selections(self):
        print("mode", self.mode.get_selected())
        print("api token", self.API_token.get_value())
        print("app id", self.app_id.get_value())
        print("symbols", self.symbols_dropdown.get_selected())
        print("trade type", self.trade_type_dropdown.get_selected())
        print("stake", self.stake.get_value())
        
        print("martingale mode", self.martingale_type.get_selected())
        print("martingale_multiplier", self.martingale_multiplier.get_value())
        print("strategy", self.strategy.get_values())
        print("trade duration", self.trade_duration.get_values())
        
        
        data = {"run_mode": self.mode.get_selected(),
            "api_token": self.API_token.get_value(),
            "app_id":self.app_id.get_value(),
            "symbols":  self.symbols_dropdown.get_selected(),
            "trade_type": self.trade_type_dropdown.get_selected(),
            "stake": self.stake.get_value(),
            "strategy": self.strategy.get_values(),
            "trade_duration": self.trade_duration.get_values(),
            "martingale":  self.martingale_type.get_selected(),
            "martingale_multiplier": self.martingale_multiplier.get_value()
        }
    
        
        strategy_list, timeframe_set = self.extract_strategy_combinations(data["strategy"])
        runtimeglobals.server_url = f"http://{self.server_url.get_value()}"
        runtimeglobals.secret_code = self.secret_code.get_value()

        print(runtimeglobals.server_url)
        print(runtimeglobals.secret_code)

        runtimeglobals.run_mode = data["run_mode"][0]
        runtimeglobals.trade_type = data["trade_type"]
        # Set runtime globals if needed
        runtimeglobals.initial_stake = data["stake"]
        runtimeglobals.current_stake = runtimeglobals.initial_stake
        runtimeglobals.API_token = data["api_token"]
        
        runtimeglobals.app_id = data["app_id"]
        
        runtimeglobals.timeframes =list(set(runtimeglobals.timeframes)|set(timeframe_set))
        
        print(runtimeglobals.timeframes)
        
        # Set runtime globals if needed
        runtimeglobals.MARKETS = data["symbols"]
        #runtimeglobals.timeframes = timeframes
        td = data["trade_duration"]
        runtimeglobals.duration_unit = "t" if "ticks" in td["parent"] else "m"
        
        runtimeglobals.duration = td["children"] ["trade duration"]
        
        runtimeglobals.trade_duration = data["trade_duration"]
        # Set runtime globals if needed
        runtimeglobals.martingale_type = data["martingale"][0]
        runtimeglobals.martingale_multiplier = int(data["martingale_multiplier"])
        # Set runtime globals if needed
        runtimeglobals.strategy = strategy_list
        runtimeglobals.market_data = {
    symbol: {
        "tick_data": deque(maxlen=1000),
        "candles_1min": deque(maxlen=1000),
        "candles_5min": deque(maxlen=1000),
        "candles_15min": deque(maxlen=1000),
        "candles_30min": deque(maxlen=1000),
        "candles_1hr": deque(maxlen=1000),
        "candles_4hr": deque(maxlen=1000),
        "candles_1day": deque(maxlen=1000),
    } for symbol in data["symbols"]
}
        print(runtimeglobals)
        
        
    
    def on_setup_complete(self, *args):
        # Create a transparent overlay with dark background
        self.loading_overlay = FloatLayout(size=self.size, pos=self.pos)
        
        with self.loading_overlay.canvas:
            Color(0.07, 0.07, 0.07, 0.95)  # Semi-transparent black
            self.overlay_bg = Rectangle(size=self.size, pos=self.pos)
    
        # Add pulsing "Loading..." label
        self.loading_label = Label(
            text="Loading main screen...",
            font_size='22sp',
            color=[1, 1, 1, 1],
            size_hint=(None, None),
            size=(self.width, 50),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
    
        self.loading_overlay.add_widget(self.loading_label)
        self.add_widget(self.loading_overlay)
    
        # Pulse animation
        anim = Animation(opacity=0.3, duration=0.5) + Animation(opacity=1, duration=0.5)
        anim.repeat = True
        anim.start(self.loading_label)
    
        # Bind to window resizing
        self.bind(size=self.update_overlay_rect, pos=self.update_overlay_rect)
    
        # Schedule transition to next screen
        Clock.schedule_once(self.close_menu, 0.4)
    
    def update_overlay_rect(self, *args):
        if hasattr(self, 'overlay_bg'):
            self.overlay_bg.size = self.size
            self.overlay_bg.pos = self.pos
    
    def close_menu(self, *args):
        from mainlayoutscreen import MainLayoutScreen

        self.print_selections()

        # Remove loading overlay
        if self.loading_overlay:
            self.remove_widget(self.loading_overlay)
            self.loading_overlay = None

        # Check if "main" screen already exists in the manager
        if not self.manager.has_screen('main'):
            main_screen = MainLayoutScreen(name='main')
            self.manager.add_widget(main_screen)

        self.manager.current = 'main'

        
        
        
"""
class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = get_color_from_hex("#000000")
        
        scroll_view = ScrollView()
        content = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        self.API_token= LabeledTextInput(label = "API TOKEN",default = "wPYKJXzoLKJYBVU")
        content.add_widget(self.API_token)
        
        self.app_id= LabeledTextInput(label = "App ID",default = "82751",input_type = int,special = True)
        content.add_widget(self.app_id)
        
        self.symbols_dropdown = CheckboxDropdown(label="Symbols", options=["R_25", "R_50", "R_75", "R_100"],default_selected=["R_25"],
    multiselect=True,
    preview_selected=True)
        content.add_widget(self.symbols_dropdown)
        
        self.trade_type_dropdown = CheckboxDropdown(label="trade type", options=["higher/lower", "rise/fall", "multipliers"],default_selected=["higher/lower"],
    multiselect=False,
    preview_selected=True)
        content.add_widget(self.trade_type_dropdown)
        
        self.martingale_type = CheckboxDropdown(label="martingale type", options=["mode_x2", "mode_x23factor", "mode_3factor"],default_selected=["mode_x2"],
    multiselect=False,
    preview_selected=True)
        content.add_widget(self.martingale_type)
        
        self.stake = LabeledTextInput(label = "Stake", input_type = float, min_value = 0.35,max_value = 1000, default = "0.35")
        content.add_widget(self.stake)
        
        self.martingale_multiplier = LabeledTextInput(label = "martingale multiplier", input_type = int, min_value = 1,max_value = 8, default = "2")
        content.add_widget(self.martingale_multiplier)
        
        self.trade_duration = Nested(
    parent_config={
        "label": "Choose trade timeframe",
        "options": ["ticks", "mins"],
        "default_selected":["ticks"],
        "multiselect": False
    },
    children_config_map={
        "ticks": [{
        "type": "textinput",
        "kwargs": {
            "label": "trade duration",
            "input_type":int,
            "min_value": 1,
            "max_value":60,
            "default" :"5",
        }
    }],
        
        "mins": [
    {
        "type": "textinput",
        "kwargs": {
            "label": "trade duration",
            "input_type":int,
            "min_value": 1,
            "max_value":60,
            "default" :"1",
        }
    }
],
        
     }  
)

        content.add_widget(self.trade_duration)
        
        self.strategy = Nested(
    parent_config={
        "label": "Choose strategy",
        "options": ["candle_color", "macd", "bollinger"],
        "default_selected":["candle_color","macd"]
    },
    children_config_map={
        "macd": [{
        "type": "checkbox",
        "kwargs": {
            "label": "macd_timeframe",
            "options": ["1min", "5min", "15min"],
            "default_selected": ["1min"]
        }
    }],
        
        "candle_color": [
    {
        "type": "checkbox",
        "kwargs": {
            "label": "candle_color_timeframe",
            "options": ["1min", "5min", "15min"],
            "default_selected": ["1min"]
        }
    }
],
        
        "bollinger": [
            {"type": "textinput", "kwargs": {"label": "BB Period"}},
            {"type": "textinput", "kwargs": {"label": "BB Deviation"}},
        ],
    }
)

        content.add_widget(self.strategy)
        # Submit Button
        submit_btn = Button(text="Save&Continue", on_release=self.on_setup_complete, size_hint_y=None, height=dp(50))
        content.add_widget(submit_btn)
        
        scroll_view.add_widget(content)
        self.add_widget(scroll_view)

    def extract_strategy_combinations(self,strategy_dict):
        strategies = []
        all_timeframes = set()
    
        for parent in strategy_dict.get("parent", []):
            key = f"{parent}_timeframe"
            timeframes = strategy_dict.get("children", {}).get(key, [])
    
            for tf in timeframes:
                strategies.append(f"{parent}_{tf}")
                all_timeframes.add(tf)
    
        return strategies, all_timeframes
    
    def print_selections(self):
        print("api token", self.API_token.get_value())
        print("app id", self.app_id.get_value())
        print("symbols", self.symbols_dropdown.get_selected())
        print("trade type", self.trade_type_dropdown.get_selected())
        print("stake", self.stake.get_value())
        
        print("martingale mode", self.martingale_type.get_selected())
        print("martingale_multiplier", self.martingale_multiplier.get_value())
        print("strategy", self.strategy.get_values())
        print("trade duration", self.trade_duration.get_values())
        
        
        data = {
            "api_token": self.API_token.get_value(),
            "app_id":self.app_id.get_value(),
            "symbols":  self.symbols_dropdown.get_selected(),
            "trade_type": self.trade_type_dropdown.get_selected(),
            "stake": self.stake.get_value(),
            "strategy": self.strategy.get_values(),
            "trade_duration": self.trade_duration.get_values(),
            "martingale":  self.martingale_type.get_selected(),
            "martingale_multiplier": self.martingale_multiplier.get_value()
        }
    
        
        strategy_list, timeframe_set = self.extract_strategy_combinations(data["strategy"])
        runtimeglobals.trade_type = data["trade_type"]
        # Set runtime globals if needed
        runtimeglobals.initial_stake = data["stake"]
        runtimeglobals.current_stake = runtimeglobals.initial_stake
        runtimeglobals.API_token = data["api_token"]
        
        runtimeglobals.app_id = data["app_id"]
        
        runtimeglobals.timeframes =list(set(runtimeglobals.timeframes)|set(timeframe_set))
        
        print(runtimeglobals.timeframes)
        
        # Set runtime globals if needed
        runtimeglobals.MARKETS = data["symbols"]
        #runtimeglobals.timeframes = timeframes
        td = data["trade_duration"]
        runtimeglobals.duration_unit = "t" if "ticks" in td["parent"] else "m"
        
        runtimeglobals.duration = td["children"] ["trade duration"]
        
        runtimeglobals.trade_duration = data["trade_duration"]
        # Set runtime globals if needed
        runtimeglobals.martingale_type = data["martingale"][0]
        runtimeglobals.martingale_multiplier = int(data["martingale_multiplier"])
        # Set runtime globals if needed
        runtimeglobals.strategy = strategy_list
        runtimeglobals.market_data = {
    symbol: {
        "tick_data": deque(maxlen=1000),
        "candles_1min": deque(maxlen=1000),
        "candles_5min": deque(maxlen=1000),
        "candles_15min": deque(maxlen=1000),
        "candles_30min": deque(maxlen=1000),
        "candles_1hr": deque(maxlen=1000),
        "candles_4hr": deque(maxlen=1000),
        "candles_1day": deque(maxlen=1000),
    } for symbol in data["symbols"]
}
        
    def on_setup_complete(self):
        loading_label = Label(text="Loading main screen...", font_size='20sp')
        self.add_widget(loading_label)
    
        Clock.schedule_once(self.close_menu, 0.1)
        
    def close_menu(self, *args):
        from mainlayoutscreen import MainLayoutScreen
        self.print_selections()
        #app = App.get_running_app()
        #app.root.current = "main"
        main_screen = MainLayoutScreen(name='main')
        self.manager.add_widget(main_screen)
        self.manager.current = 'main'
"""        
      
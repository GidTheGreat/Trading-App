from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line
from kivy.uix.widget import Widget
from livebackground import LiveBackground
from gridcanvas import GridCanvas
from masterchart import MasterChart
from status_manager import StatusDisplayManager
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from debug_summary import build_debug_summary
from kivy.app import App
from botutils import runtimeglobals
from kivy.uix.button import Button
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
import sys
from marquee import MarqueeLabel

# Global height ratio for sections: Top, Middle, Bottom, Buttons
section_ratios = [1, 6, 3, 1]



class SectionWrapper(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(1, 1, 1, 0.1)  # Subtle white border
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=1)
        self.bind(pos=self._update_border, size=self._update_border)

    def _update_border(self, *args):
        self.border.rectangle = (self.x, self.y, self.width, self.height)


class MainLayout(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background = LiveBackground()
        self.add_widget(self.background)

        self.fg_layout = GridLayout(cols=1, rows=4, size_hint=(1, 1))
        self.add_widget(self.fg_layout)

        total_ratio = sum(section_ratios)

        # === Top Section ===
        self.top_section = SectionWrapper()
        self.top_section.size_hint_y = section_ratios[0] / total_ratio
        marquee_container = FloatLayout(size_hint=(1, 1))  # Fills SectionWrapper

        # Add marquee label
        marquee_label = MarqueeLabel(
            text="Trading beyond the event horizon",
            font_size='22sp',
            color=(0.0, 0.1, 0.3, 1),  # Neon cyan
            bold=True,
            halign="center",
            valign="middle",
            markup=True,
            shorten=False
        )

        marquee_container.add_widget(marquee_label)

        # Add everything to layout
        self.top_section.add_widget(marquee_container)
        self.fg_layout.add_widget(self.top_section)

        # === Middle Section ===
        self.middle_section = SectionWrapper()
        self.middle_section.size_hint_y = section_ratios[1] / total_ratio
        self.chart_canvas = GridCanvas()
        self.middle_section.add_widget(self.chart_canvas)
        self.chart = MasterChart(container=self.chart_canvas)
        self.chart_canvas.add_widget(self.chart)
        self.status_display = StatusDisplayManager(self, chart=self.chart)

        Clock.schedule_interval(self.status_display.update, 0.5)

        self.fg_layout.add_widget(self.middle_section)

        # === Bottom Section ===
        self.bottom_section = SectionWrapper()
        self.bottom_section.size_hint_y = section_ratios[2] / total_ratio

        self.bottom_grid = GridLayout(cols=2, size_hint=(1, 1))

        # --- Bottom Left ---
        self.bottom_left = BoxLayout()
        scroll_view_left = ScrollView(do_scroll_x=True, do_scroll_y=True)

        self.scroll_content_left = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint=(None, None)
        )
        self.scroll_content_left.bind(
            minimum_height=self.scroll_content_left.setter("height"),
            minimum_width=self.scroll_content_left.setter("width")
        )

        self.status_logs = Label(
            text="Log: --",
            size_hint_y=None,
            halign='left',
            valign='top',
        )
        self.status_logs.bind(
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )

        self.debug_summary = build_debug_summary()

        self.scroll_content_left.add_widget(self.status_logs)
        self.scroll_content_left.add_widget(self.debug_summary)

        scroll_view_left.add_widget(self.scroll_content_left)
        self.bottom_left.add_widget(scroll_view_left)

        # --- Bottom Right (ScrollView) ---
        scroll_view_right = ScrollView(do_scroll_y=True)
        self.scroll_content_right = BoxLayout(
            orientation="vertical",
            spacing=dp(5),
            padding=dp(5),
            size_hint_y=None
        )
        self.scroll_content_right.bind(
            minimum_height=self.scroll_content_right.setter("height")
        )

        def section_label(text):
            return Label(
                text=text,
                color=(0.4, 0.8, 1, 1),
                bold=True,
                font_size='20sp',
                size_hint_y=None
            )

        # Current Trade
        self.scroll_content_right.add_widget(section_label("Current Trade"))
        self.entry_label = self._left_aligned_label("Entry: --")
        self.current_label = self._left_aligned_label("Current: --")
        self.exit_label = self._left_aligned_label("Exit: --")
        self.pnl_label = self._left_aligned_label("P&L: --")
        for lbl in [self.entry_label, self.current_label, self.exit_label, self.pnl_label]:
            self.scroll_content_right.add_widget(lbl)

        # Stats
        self.scroll_content_right.add_widget(section_label("Stats"))
        self.won_label = self._left_aligned_label("Won: --")
        self.total_label = self._left_aligned_label("Total Trades: --")
        self.pl_label = self._left_aligned_label("Total P/L: --")
        self.stake_label = self._left_aligned_label("Current Stake: --")
        self.loss_streak_label = self._left_aligned_label("Loss Streak: --")
        for lbl in [self.won_label, self.total_label, self.pl_label, self.stake_label, self.loss_streak_label]:
            self.scroll_content_right.add_widget(lbl)

        scroll_view_right.add_widget(self.scroll_content_right)
        self.bottom_grid.add_widget(self.bottom_left)
        self.bottom_grid.add_widget(scroll_view_right)
        self.bottom_section.add_widget(self.bottom_grid)

        self.fg_layout.add_widget(self.bottom_section)

        # === Button Section ===
        self.button_section = SectionWrapper()
        self.button_section.size_hint_y = section_ratios[3] / total_ratio

        self.button_grid = GridLayout(cols=4, spacing=10, padding=10)
        self.btn = Button(text="Launch Bot UI", 
        background_color=(0.2, 0.6, 0.2, 1))
        self.btn2 = Button(text="Reload Server",
        background_color=(0.6, 0.2, 0.2, 1))
        self.button_grid.add_widget(self.btn)
        # Periodic sync check for analysis state
        Clock.schedule_interval(self._sync_button_state, 0.5)

        self.button_grid.add_widget(self.btn2)
    
        self.btn.bind(on_release=self.launch_bot_ui)
        self.btn2.bind(on_release=self.reload_server)
        self.button_section.add_widget(self.button_grid)
        self.fg_layout.add_widget(self.button_section)

    
    def _sync_button_state(self, dt):
        client_available = sys.modules.get("client") is not None
        self.btn.disabled = runtimeglobals.analysis_running
        if client_available:
            self.btn2.disabled = False
        else:
            self.btn2.disabled = True

    def reload_server(self, instance):
        client = sys.modules.get("client")
        if client:
            client.reload_server()
        else:
            print("⚠️ client module not loaded in sys.modules")
    def launch_bot_ui(self, instance):
        app = App.get_running_app()
        app.root.current = "setup"

    def _left_aligned_label(self, text):
        label = Label(
            text=text,
            size_hint_y=None,
            halign='left',
            valign='top',
        )
        label.bind(
            width=lambda instance, value: setattr(instance, 'text_size', (value, None)),
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )
        return label
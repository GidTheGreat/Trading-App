from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

def hex_rgba(hex_color, alpha=1.0):
    color = get_color_from_hex(hex_color)
    color[3] = alpha
    return color

def build_debug_summary(symbol="R_25", time_str="2025-07-26 13:50:00",
                        strategy_data=None, final_decision="CALL"):

    if strategy_data is None:
        strategy_data = [
            ("MACD", "RED", "PUT"),
            ("RSI", "40", "PUT"),
            ("Bollinger", "Reentry....", "CALM")
        ]

    # Color mapping
    decision_colors = {
        "PUT": hex_rgba("#FF4C4C"),
        "CALL": hex_rgba("#4CFF4C"),
        "CALM": hex_rgba("#FFD700"),
        "N/A": hex_rgba("#AAAAAA"),
    }

    def fixed_label(text, width=dp(100), color=hex_rgba("#E0E0E0")):
        return Label(
            text=text,
            halign='left',
            valign='middle',
            size_hint=(None, None),
            size=(width, dp(25)),
            text_size=(width, dp(25)),
            shorten=True,
            max_lines=1,
            color=color,
            markup=True,
        )

    debug_summary = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
    debug_summary.bind(minimum_height=debug_summary.setter('height'))

    # Meta info
    debug_summary.add_widget(fixed_label(f"[b]Symbol:[/b] {symbol}", width=dp(250), color=hex_rgba("#BBBBFF")))
    debug_summary.add_widget(fixed_label(f"[b]Time:[/b] {time_str}", width=dp(250), color=hex_rgba("#BBBBFF")))

    # Header
    header = GridLayout(cols=3, size_hint_y=None, height=dp(25), spacing=dp(5))
    header.add_widget(fixed_label("[b]Strategy[/b]", width=dp(100), color=hex_rgba("#FFD700")))
    header.add_widget(fixed_label("[b]Raw[/b]", width=dp(100), color=hex_rgba("#FFD700")))
    header.add_widget(fixed_label("[b]Decision[/b]", width=dp(100), color=hex_rgba("#FFD700")))
    debug_summary.add_widget(header)

    # Strategy rows
    strategy_rows = GridLayout(cols=3, size_hint_y=None, spacing=dp(5))
    for name, raw, decision in strategy_data:
        strategy_rows.add_widget(fixed_label(name))
        strategy_rows.add_widget(fixed_label(str(raw)))
        color = decision_colors.get(decision.upper(), hex_rgba("#AAAAAA"))
        strategy_rows.add_widget(fixed_label(decision, color=color))
    strategy_rows.bind(minimum_height=strategy_rows.setter('height'))
    debug_summary.add_widget(strategy_rows)

    # Final decision
    final = GridLayout(cols=2, size_hint_y=None, height=dp(25), spacing=dp(5))
    final.add_widget(fixed_label("Final Decision:", width=dp(100), color=hex_rgba("#FFD700")))
    final_decision = "N/A" if final_decision is None else final_decision
    color = decision_colors.get(final_decision.upper(), hex_rgba("#AAAAAA"))
    final.add_widget(fixed_label(f"[b]{final_decision}[/b]", width=dp(200), color=color))
    debug_summary.add_widget(final)

    return debug_summary
    
    
    
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import dp

def build_debug_summary(symbol="BTCUSDT", time_str="2025-07-26 13:50:00",
                        strategy_data=None, final_decision="STRONG BUY"):
    if strategy_data is None:
        strategy_data = [
            ("MACD", "1.5", "BUY"),
            ("RSI", "72", "SELL"),
            ("Bollinger", "-0.3", "HOLD")
        ]

    def left_label(text):
        return Label(text=text, halign='left', valign='middle', size_hint_y=None, height=dp(25), text_size=(None, None))

    debug_summary = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
    debug_summary.bind(minimum_height=debug_summary.setter('height'))

    debug_summary.add_widget(left_label(f"Symbol: {symbol}"))
    debug_summary.add_widget(left_label(f"Time: {time_str}"))

    header = GridLayout(cols=3, size_hint_y=None, height=dp(25), spacing=dp(5))
    header.add_widget(Label(text="[b]Strategy[/b]", markup=True))
    header.add_widget(Label(text="[b]Raw[/b]", markup=True))
    header.add_widget(Label(text="[b]Decision[/b]", markup=True))
    debug_summary.add_widget(header)

    strategy_rows = GridLayout(cols=3, size_hint_y=None, spacing=dp(5))
    for name, raw, decision in strategy_data:
        strategy_rows.add_widget(left_label(name))
        strategy_rows.add_widget(left_label(str(raw)))
        strategy_rows.add_widget(left_label(decision))
    debug_summary.add_widget(strategy_rows)

    final = GridLayout(cols=2, size_hint_y=None, height=dp(25), spacing=dp(5))
    final.add_widget(left_label("Final Decision:"))
    final.add_widget(left_label(final_decision))
    debug_summary.add_widget(final)

    return debug_summary
"""
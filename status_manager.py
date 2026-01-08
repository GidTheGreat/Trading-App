# status_manager.py
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp
from botutils import status
from kivy.clock import Clock
from debug_summary import build_debug_summary  # Replace with actual module path

class StatusDisplayManager:
    def __init__(self, root, chart=None):
        self.root = root
        self.chart = chart
        self.excluded_categories = ["ticks"]
        self.last_unspecified_log = ""
        self.general_categories = ["trades", "INIT", "heartbeat"]

    def update(self, dt):
        y_pos = 0.9

        for category, message in status.status_messages.items():
            if category in self.excluded_categories:
                if isinstance(message, dict):
                    for sub_key, tick in message.items():
                        if isinstance(tick, dict) and "quote" in tick and "epoch" in tick:
                            symbol = sub_key.replace("tick_", "").replace("symbol_", "")
                            if self.chart:
                                self.chart.add_tick(symbol, tick["quote"], tick["epoch"])
                continue

            if category == "candles":
                for key, value in message.items():
                    if self.chart:
                        self.chart.add_candle_data(category, key, value)
                continue

            if category == "tick_entries" and isinstance(message, dict) and "tracker" in message:
                tracker_text = message["tracker"]
                try:
                    parts = tracker_text.split("|")
                    entry = parts[1].split(":")[1].strip()
                    current = parts[2].split(":")[1].strip()
                    exit = parts[3].split(":")[1].strip()
                    pnl = parts[4].split(":")[1].strip()

                    if hasattr(self.root, "entry_label"):
                        self.root.entry_label.text = f"Entry: {entry}"

                    if hasattr(self.root, "current_label"):
                        self.root.current_label.text = f"Current: {current} "
                    if hasattr(self.root, "exit_label"):
                        self.root.exit_label.text = f"Exit: {exit}"
                    if hasattr(self.root, "pnl_label"):
                        pnl_float = float(pnl)
                        color = (0, 1, 0, 1) if pnl_float >= 0 else (1, 0, 0, 1)
                        self.root.pnl_label.text = f"P&L: {pnl}"
                        self.root.pnl_label.color = color
                except Exception as e:
                    print(f"[tick_entries.tracker Parse Error] {e}")
                continue

            if category == "profit_loss" and isinstance(message, dict) and "winstats" in message:
                winstext = message["winstats"]
                try:
                    stats = {part.split(":")[0].strip(): part.split(":")[1].strip() for part in winstext.split("|")}

                    if hasattr(self.root, "won_label"):
                        self.root.won_label.text = f"Won: {stats.get('Total Wins', '--')}"
                    if hasattr(self.root, "total_label"):
                        self.root.total_label.text = f"Total Trades: {stats.get('Total Trades', '--')}"
                    if hasattr(self.root, "pl_label"):
                        self.root.pl_label.text = f"Total P/L: {stats.get('Total P/L', '--')}"
                    if hasattr(self.root, "stake_label"):
                        self.root.stake_label.text = f"Current Stake: {stats.get('Current Stake', '--')}"
                    if hasattr(self.root, "loss_streak_label"):
                        self.root.loss_streak_label.text = f"Loss Streak: {stats.get('Max Loss Streak', '--')}"
                except Exception as e:
                    print(f"[profit_loss.winstats Parse Error] {e}")
                continue

            if category == "debug_summary" and isinstance(message, dict) and "summary" in message:
                debug_data = message["summary"]
                try:
                    if isinstance(debug_data, dict):
                        symbol = debug_data.get("symbol", "N/A")
                        timestamp = debug_data.get("timestamp", "N/A")
                        final_decision = debug_data.get("final_decision", "N/A")
                        strategies = debug_data.get("strategies", {})

                        strategy_data = []
                        for strat, result in strategies.items():
                            raw = result.get("raw", "?")
                            decision = result.get("decision", "?")
                            strategy_data.append((strat, str(raw), decision))

                        def update_debug_ui(dt):
                            if hasattr(self.root, "debug_summary"):
                                if self.root.debug_summary in self.root.scroll_content_left.children:
                                    self.root.scroll_content_left.remove_widget(self.root.debug_summary)

                            self.root.debug_summary = build_debug_summary(
                                symbol=symbol,
                                time_str=timestamp,
                                strategy_data=strategy_data,
                                final_decision=final_decision
                            )

                            self.root.scroll_content_left.add_widget(self.root.debug_summary)

                        Clock.schedule_once(update_debug_ui)

                except Exception as e:
                    print(f"[debug_summary.summary Parse Error] {e}")
                continue

            if category in self.general_categories:
                if isinstance(message, dict):
                    formatted = "\n".join(f"[{category}:{k}] {v}" for k, v in message.items())
                else:
                    formatted = f"[{category}] {message}"

                self.root.status_logs.text = formatted
            
            

    
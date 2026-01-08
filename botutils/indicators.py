
import pandas as pd

def calculate_macd_for_all(symbol, market_data, status_messages, timeframes, fast=12, slow=26, signal=9):
    """
    Calculates MACD for tick data and each provided timeframe,
    updates status_messages["indicators"] for each.
    """
    # Ensure base storage
    status_messages.setdefault("indicators", {})

    def calculate_and_store(close_prices, timestamps, tf_label):
        if len(close_prices) < max(slow, signal) + 2:
            return

        close_series = pd.Series(close_prices)
        ema_fast = close_series.ewm(span=fast, adjust=False).mean()
        ema_slow = close_series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        x_data = timestamps[-len(macd_line):]
        macd_plot = [{"epoch": x, "value": float(y)} for x, y in zip(x_data, macd_line)]
        signal_plot = [{"epoch": x, "value": float(y)} for x, y in zip(x_data, signal_line)]
        hist_plot = [{"epoch": x, "value": float(y)} for x, y in zip(x_data, histogram)]

        key = f"indicator_{symbol}_{tf_label}"
        status_messages["indicators"].setdefault(key, {})["macd"] = {
            "macd_line": macd_plot,
            "signal_line": signal_plot,
            "histogram": hist_plot
        }

    # Tick-based MACD
    tick_data = market_data[symbol].get("tick_data", [])
    close_prices = [tick["quote"] for tick in tick_data if "quote" in tick]
    timestamps = [tick["epoch"] for tick in tick_data]
    calculate_and_store(close_prices, timestamps, "tick")

    # Candle-based MACD for each timeframe
    for tf in timeframes:
        tf_key = f"candles_{tf}"
        candle_data = market_data[symbol].get(tf_key, [])
        close_prices = [c["close"] for c in candle_data if "close" in c]
        timestamps = [c["epoch"] for c in candle_data if "epoch" in c]
        calculate_and_store(close_prices, timestamps, tf)



def get_rsi(close_prices, period=14):
    close = pd.Series(close_prices)
    delta = close.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Wilder's smoothing
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


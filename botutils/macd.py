import pandas as pd
from botutils import runtimeglobals

def calculate_macd(tf, data,  fast=12, slow=26, signal=9):
    close_prices = []
    if tf == "tick":
        tick_data = data["tick_data"]
        tick_prices = [t["quote"] for t in tick_data]
        close_prices = tick_prices
    
    else: 
        candles =  list(data.get(f"candles_{tf}", []))
        candle_closes = [c["close"] for c in candles]
        close_prices = candle_closes
    close_series = pd.Series(close_prices)

    # Calculate EMAs
    ema_fast = close_series.ewm(span=fast, adjust=False).mean()
    ema_slow = close_series.ewm(span=slow, adjust=False).mean()

    # MACD line = EMA(fast) - EMA(slow)
    macd_line = ema_fast - ema_slow

    # Signal line = EMA of MACD line
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # Histogram = MACD - Signal
    histogram = macd_line - signal_line

    # Latest and previous values
    latest_macd = macd_line.iloc[-1]
    prev_macd = macd_line.iloc[-2]
    latest_signal = signal_line.iloc[-1]
    prev_signal = signal_line.iloc[-2]
    latest_hist = histogram.iloc[-1]
    prev_hist = histogram.iloc[-2]

    # Crossovers
    crossover_up = prev_macd < prev_signal and latest_macd > latest_signal
    crossover_down = prev_macd > prev_signal and latest_macd < latest_signal

    # Histogram color logic
    histogram_color = "GREEN" if latest_hist > prev_hist else "RED"

    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
        "crossover_up": crossover_up,
        "crossover_down": crossover_down,
        "histogram_color": histogram_color
    }

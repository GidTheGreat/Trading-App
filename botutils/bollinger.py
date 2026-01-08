from collections import deque
import pandas as pd
from ta.volatility import BollingerBands
import asyncio
import numpy as np
import time

# Settings
bollinger_period = 20
bollinger_std = 2.0
min_ticks_required = 50

# Global tracking states
band_break_state = {}
bollinger_signal = {}
bollinger_lock = asyncio.Lock()

async def analyze_bollinger_reentry(symbol, tf, data):
    global bollinger_signal, band_break_state

    if symbol not in bollinger_signal:
        bollinger_signal[symbol] = {"signal": None, "timestamp": 0}
    if symbol not in band_break_state:
        band_break_state[symbol] = None

    close_prices = []
    reference_point = None

    # Process tick data
    if tf == "tick":
        tick_data = data.get("tick_data", [])
        if len(tick_data) < min_ticks_required:
            return None

        last_tick = tick_data[-1]
        reference_point = last_tick_price = last_tick["quote"]
        close_prices = [tick["quote"] for tick in tick_data][-300:]

    # Process candle data
    else:
        candles = list(data.get(f"candles_{tf}", []))
        if len(candles) < min_ticks_required:
            return None

        reference_point = last_candle_close = candles[-1]["close"]
        close_prices = [candle["close"] for candle in candles][-300:]

    # Ensure enough data for Bollinger
    if len(close_prices) < bollinger_period:
        return None

    # Compute Bollinger Bands
    close_series = pd.Series(np.array(close_prices))
    bb = BollingerBands(close=close_series, window=bollinger_period, window_dev=bollinger_std)

    upper = bb.bollinger_hband().iloc[-1]
    prev_upper = bb.bollinger_hband().iloc[-2]
    lower = bb.bollinger_lband().iloc[-1]
    prev_lower = bb.bollinger_lband().iloc[-2]

    signal = None
    current_time = time.time()

    async with bollinger_lock:
        prev_state = band_break_state[symbol]

        # Initial breakout
        if prev_state is None:
            if reference_point > upper:
                band_break_state[symbol] = "upper"
                signal = "Break above upper band"
            elif reference_point < lower:
                band_break_state[symbol] = "lower"
                signal = "Break below lower band"

        # Re-entry from upper band
        elif prev_state == "upper" and reference_point < prev_upper:
            band_break_state[symbol] = None
            signal = "Re-entry below upper band"

        # Re-entry from lower band
        elif prev_state == "lower" and reference_point > prev_lower:
            band_break_state[symbol] = None
            signal = "Re-entry above lower band"

        # Update signal with timestamp if any
        if signal:
            bollinger_signal[symbol] = {
                "signal": signal,
                "timestamp": current_time
            }
            return signal

        # Return recent signal if still valid
        else:
            existing = bollinger_signal[symbol]
            if existing["signal"] and (current_time - existing["timestamp"]) <= 2:
                return existing["signal"]
            else:
                bollinger_signal[symbol] = {"signal": None, "timestamp": 0}

    return None

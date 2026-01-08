import asyncio
from datetime import datetime
from collections import deque 

def populate_candle_prices(market_data, candle_open_prices, candle_high_prices, candle_low_prices, timeframes):
    timeframe_key_map = {
        "1min": "candles_1min",
        "5min": "candles_5min",
        "15min": "candles_15min",
        "30min": "candles_30min",
        "1hr": "candles_1hr",
        "4hr": "candles_4hr"
    }

    for symbol in market_data:
        if symbol not in candle_open_prices:
            candle_open_prices[symbol] = {}
            candle_high_prices[symbol] = {}
            candle_low_prices[symbol] = {}

        for tf in timeframes:
            tf_key = timeframe_key_map.get(tf)
            if not tf_key:
                continue

            candles = market_data[symbol].get(tf_key, deque())
            if candles:
                print(candle_open_prices)
                last_candle = candles[-1]
                candle_open_prices[symbol][tf] = last_candle.get("open")
                candle_high_prices[symbol][tf] = last_candle.get("high")
                candle_low_prices[symbol][tf] = last_candle.get("low")
                candles.pop()  # Efficient O(1) removal for deque
                
                print(f"[{symbol}][{tf}] Open: {candle_open_prices[symbol][tf]}, High: {candle_high_prices[symbol][tf]}, Low: {candle_high_prices[symbol][tf]} | Candle popped.")
                print(candle_open_prices)
            else:
                candle_open_prices[symbol][tf] = None
                candle_high_prices[symbol][tf] = None
                candle_low_prices[symbol][tf] = None

def update_candle_open_prices(symbol, market_data, candle_open_prices):
    """
    Updates candle_open_prices for each timeframe when a new candle starts.
    Uses '1min' style keys and only sets open price at the exact rollover second.
    """
    # Ensure the symbol dict exists
    if symbol not in candle_open_prices:
        candle_open_prices[symbol] = {}

    tick_data = market_data.get(symbol, {}).get("tick_data", [])
    if not tick_data:
        return  # No tick data to process

    last_tick = tick_data[-1]
    last_epoch = last_tick["epoch"]
    last_quote = last_tick["quote"]

    timeframe_seconds = {
        "1min": 60,
        "5min": 300,
        "15min": 900,
        "30min": 1800,
        "1hr": 3600,
        "4hr": 14400,
    }

    for tf, tf_sec in timeframe_seconds.items():
        tf_price_key = tf  # e.g. "1min"
        tf_epoch_key = f"{tf}_epoch"

        # Initialize keys if needed
        if tf_price_key not in candle_open_prices[symbol]:
            candle_open_prices[symbol][tf_price_key] = None
        if tf_epoch_key not in candle_open_prices[symbol]:
            candle_open_prices[symbol][tf_epoch_key] = None

        # Check if we're at the start of a new candle for this timeframe
        if last_epoch % tf_sec == 0:
            # Only update if we haven't already for this epoch
            if candle_open_prices[symbol][tf_epoch_key] != last_epoch:
                candle_open_prices[symbol][tf_price_key] = last_quote
                candle_open_prices[symbol][tf_epoch_key] = last_epoch
                print(f"[{symbol}] ✅ New {tf} candle | Open price: {last_quote}",end="", flush=True)

def unix_converter(timestamp):
    readable_time = datetime.fromtimestamp(timestamp)
    return readable_time.strftime('%Y-%m-%d %H:%M:%S')


#================ START OF CANDLE ANALYSIS BLOCK ================================================================
def get_candle_open_epoch(tick_epoch: int, timeframe: str) -> int:
    
    """Rounds tick_epoch to the start epoch of the current candle for a given timeframe."""
    tf_map = {
        "1min": 60,
        "5min": 300,
        "15min": 900,
        "30min":1800,
        "1hr": 3600,
        "4hr": 14400,
        
    }
    interval = tf_map[timeframe]
    #print(unix_converter(tick_epoch - (tick_epoch % interval)))
    return tick_epoch - (tick_epoch % interval)

async def update_candle_status_all_timeframes(symbol,market_data,timeframes,stop_event,candle_open_prices, status_messages):
    """Tracks forming and completed candles across multiple timeframes."""
    
    while not stop_event.is_set():
        if not market_data[symbol]["tick_data"]:
            
            await asyncio.sleep(1)
            continue

        last_tick = market_data[symbol]["tick_data"][-1]
        tick_price = last_tick["quote"]
        tick_time = last_tick["epoch"]

        for tf in timeframes:
            open_epoch = get_candle_open_epoch(tick_time, tf)
            if market_data[symbol].get(f"last_candle_epoch_{tf}") != open_epoch:
                await start_new_candle(symbol, market_data, tf, tick_price, open_epoch, candle_open_prices)


            await update_candle_state_and_color(symbol, market_data, tf, tick_price, tick_time,status_messages)

        await asyncio.sleep(1)

async def start_new_candle(symbol, market_data, tf, tick_price, open_epoch, candle_open_prices):
    """Handles initialization of a new candle, and stores the open price."""
    tf_key = f"candles_{tf}"
    forming_key = f"forming_candle_{tf}"
    last_epoch_key = f"last_candle_epoch_{tf}"
    completed_key = f"last_completed_candle_{tf}"

    if market_data[symbol].get(forming_key):
        market_data[symbol][completed_key] = market_data[symbol][forming_key]
        market_data[symbol][tf_key].append(market_data[symbol][completed_key])

    market_data[symbol][last_epoch_key] = open_epoch

    # Recheck open price from candle_open_prices or fallback to tick
    open_price = candle_open_prices.get(symbol, {}).get(tf, tick_price)
    print(f"\r{symbol} | Open ({tf}): {open_price}", end="", flush=True)

    market_data[symbol][forming_key] = {
        "open": open_price,
        "high": open_price,
        "low": open_price,
        "close": tick_price,
        "epoch": open_epoch
    }



async def update_candle_state_and_color(symbol, market_data, tf, tick_price, tick_time,status_messages):
    """Safely updates the forming candle and color, handles errors gracefully."""
    tf_map = {
        "1min": 60,
        "5min": 300,
        "15min": 900,
        "30min": 1800,
        "1hr": 3600,
        "4hr": 14400,
    }
    try:
        forming_key = f"forming_candle_{tf}"
        completed_key = f"last_completed_candle_{tf}"
        color_key = f"tick_color_{tf}"
        last_epoch_key = f"last_candle_epoch_{tf}"

        forming = market_data[symbol].get(forming_key)
        if not forming:
            return  # No candle to update yet

        # Safe updates
        forming["high"] = max(forming.get("high", tick_price), tick_price)
        forming["low"] = min(forming.get("low", tick_price), tick_price)
        forming["close"] = tick_price

        # Determine color
        prev_candle = market_data[symbol].get(completed_key)
        prev_color = "GREEN" if prev_candle and prev_candle["close"] > prev_candle["open"] else "RED"
        curr_color = "GREEN" if forming["close"] > forming["open"] else "RED"
        market_data[symbol][color_key] = curr_color

        # Time remaining
        open_epoch = market_data[symbol].get(last_epoch_key)
        if open_epoch is None:
            return  # avoid math with None

        # In your candle loop:
        tf_seconds = tf_map[tf]
        open_epoch = get_candle_open_epoch(tick_time, tf)
        next_epoch = open_epoch + tf_seconds
        time_left = next_epoch - tick_time
        time_str = format_time_left(time_left)
        values = {
                "prev_color": prev_color,
                "curr_color": curr_color,
                "time_left": time_str
            }
        formatted_msg = f"{symbol}, tf:{tf} | " + " | ".join(f"{k}:{v}" for k, v in values.items())
        # Push latest 50 completed candles
        completed = list(market_data[symbol].get(f"candles_{tf}", []))[-50:]
        forming = market_data[symbol].get(f"forming_candle_{tf}", {})

        status_messages["candles"][f"candles_{symbol}_{tf}"] = completed
        status_messages["candles"][f"forming_{symbol}_{tf}"] = forming

        

        
    except Exception as e:
        status_messages["candles"][f"candles_1min"] = (
                f"[ERROR] Failed to update candle: {e}"
            )
        
        

def format_time_left(seconds):
    """Converts seconds into 'xh ym zs' format."""
    seconds = int(seconds)
    parts = []
    for label, unit in [("h", 3600), ("m", 60), ("s", 1)]:
        val, seconds = divmod(seconds, unit)
        if val > 0 or label == "s":  # Always show seconds
            parts.append(f"{val}{label}")
    return " ".join(parts)

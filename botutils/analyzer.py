import asyncio
from typing import Dict, Optional
from botutils import runtimeglobals
from botutils.place_trade import place_trade
from datetime import datetime,timedelta,timezone
from botutils.status import status_messages
from botutils.macd import calculate_macd
from botutils.bollinger import analyze_bollinger_reentry

trade_lock = asyncio.Lock()


# --- Strategy-specific resolvers ---

async def get_prev_candle_color(data: dict, tf: str) -> Optional[str]:
    key = f"candles_{tf}"
    if key not in data or not data[key]:
        return None
    candle = data[key][-1]
    return "GREEN" if candle["close"] > candle["open"] else "RED"


async def histogram_color(data: dict, tf: str):
    data = calculate_macd(tf, data)
    return data["histogram_color"]

async def crossover_status(data, tf):
    data = calculate_macd(tf, data)
    if data["crossover_down"]:
        return "crossover down"
    if data["crossover_up"]:
        return "crossover up"
    return None

async def macd_momentum(data: dict, tf: str):
    data = calculate_macd(tf, data)
    if data["macd_line"].iloc[-1] < data["signal_line"].iloc[-1]:
        return "bearish"
    if data["macd_line"].iloc[-1] > data["signal_line"].iloc[-1]:
        return "bullish"
    
            

# --- Decision logic ---

def convert_to_decision(strategy_name: str, value) -> Optional[str]:
    """Translate raw strategy result into a CALL or PUT decision."""
    print(f"value:{value} ,strategy_name:{strategy_name}")
    if not value:
        return None

    # Normalize strategy name (e.g., remove '_1min', '_5min' suffixes)
    base_name = strategy_name.split('_')[0]

    if base_name == "candle":
        base_name = "candle_color"  # for candle_color_1min, etc.
    if base_name == "color":
        base_name = "color_stability" 
    decision_map = {
        'prev': {"RED": "PUT", "GREEN": "CALL"},
        'candle_color': {"RED": "PUT", "GREEN": "CALL"},
        'macdhistogram': {"RED": "PUT", "GREEN": "CALL"},
        'macdmomentum': {
            "bearish": "PUT",
            "bullish": "CALL"
        },
        'bollinger': {
            "Re-entry below upper band": "PUT",
            "Re-entry above lower band": "CALL"
        },
        'macdcrossover': {
            "crossover down": "PUT",
            "crossover up": "CALL"
        },
        
        'color_stability': {
            "BULLISH": "CALL",
            "BEARISH": "PUT"
        }
    }

    # Match against normalized keys
    for key, mapping in decision_map.items():
        #print(f"key:{key}")
        
        if base_name.startswith(key):
            #print(f"base_name:{base_name}")
            #print(base_name.startswith(key))
            return mapping.get(value)

    return None


def generate_tf_strategies(symbol: str, data: dict, stop_event):
    strategies = {}
    print(f"DEBUG TIMEFRAMES:{runtimeglobals.timeframes}")
    for tf in runtimeglobals.timeframes:
        tf_key = tf.replace("min", "m").replace("hr", "h")

        strategies[f"prev_candle_color_{tf}"] = {
            "active": f"prev_candle_color_{tf}" in runtimeglobals.strategy,
            "resolver": lambda tf=tf: get_prev_candle_color(data, tf),
            "needs_symbol": False,
        }

        strategies[f"candle_color_{tf}"] = {
            "active": f"candle_color_{tf}" in runtimeglobals.strategy,
            "resolver": lambda tf=tf: data.get(f"tick_color_{tf}"),
            "needs_symbol": False,
        }

        strategies[f"macdmomentum_{tf}"] = {
            "active": f"macdmomentum_{tf}" in runtimeglobals.strategy,
            "resolver": lambda tf=tf: macd_momentum(data, tf),
            "needs_symbol": False,
        }
        
        strategies[f"macdcrossover_{tf}"] = {
            "active": f"macdcrossover_{tf}" in runtimeglobals.strategy,
            "resolver": lambda tf=tf: crossover_status(data, tf),
            "needs_symbol": False,
        }
        
        strategies[f"macdhistogram_{tf}"] = {
            "active": f"macdhistogram_{tf}" in runtimeglobals.strategy,
            "resolver": lambda tf=tf: histogram_color(data, tf),
            "needs_symbol": False,
        }

        strategies[f"bollinger_{tf}"] = {
            "active": f"bollinger_{tf}" in runtimeglobals.strategy,
            "resolver": lambda tf=tf: analyze_bollinger_reentry(symbol, tf, data),
            "needs_symbol": True,
        }

   
    return strategies

async def analyzed_trade(symbol: str, stop_event) -> Optional[str]:
    data = runtimeglobals.market_data[symbol]
    debug_data = {
        'symbol': symbol,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'strategies': {}
    }

    STRATEGIES = generate_tf_strategies(symbol, data, stop_event)
    active_decisions = {}

    for name, strat in STRATEGIES.items():
        #print(STRATEGIES)
        #print(strat)
        #print(f"name:{name}")
        if not strat['active']:
            continue
        try:
            result = strat['resolver']()
            
            if asyncio.iscoroutine(result):
                result = await result
                print("result:",result)
                

            #socketio.emit("bot_message",["strategy_raw", name, f"{result} on {symbol}"])

            decision = convert_to_decision(name, result)
            debug_data['strategies'][name] = {'raw': result, 'decision': decision}

            if decision:
                print("bot_message",["strategy_decision", name, decision])
                active_decisions[name] = decision
            else:
                print("bot_message",["strategy_decision", name, "NO_DECISION"])

        except Exception as e:
            error_msg = f"{name} error: {str(e)}"
            print("bot_message",["error", name, error_msg])
            debug_data['strategies'][name] = {'error': error_msg}

    expected = [k for k, v in STRATEGIES.items() if v["active"]]
    #print(f"active:{active_decisions},expected:{expected}")
    if len(active_decisions) != len(expected):
        return None

    final_decision = resolve_combined_decision(active_decisions)
    debug_data["final_decision"] = final_decision

    print(debug_data)
    print("bot_message",["debug_summary", "summary", debug_data])
    status_messages["debug_summary"]["summary"] = debug_data
    status_messages
    return final_decision

def resolve_combined_decision(strategies: Dict[str, str]) -> Optional[str]:
    """Strict decision resolution with validation."""
    if not strategies:
        return None
        
    # Validate all decisions are PUT/CALL
    valid_decisions = {"PUT", "CALL"}
    decisions = []
    
    for name, decision in strategies.items():
        if decision not in valid_decisions:
            return None
        decisions.append(decision)
    
    # Check consensus
    unique_decisions = set(decisions)
    return unique_decisions.pop() if len(unique_decisions) == 1 else None

async def one_tick_entry(symbol,stop_event):
    if "debug_summary" not in status_messages:
        status_messages["debug_summary"] = {}
    status_messages["INIT"]= f"{runtimeglobals.strategy}"   
    if runtimeglobals.active_trade:
        return  # Block new trades if one is active

    async with trade_lock:  # Prevents simultaneous trade execution
        if runtimeglobals.active_trade:  # Double-check inside lock
            return

        if "random" in runtimeglobals.strategy:
            choice = random_trade()
            trade_direction = choice
        
        else:
            trade_direction = await analyzed_trade(symbol, stop_event)

        if trade_direction:     
            runtimeglobals.active_trade = True
            await place_trade(symbol, trade_direction)
            print("bot_message",["type_of_trade",f"entry", f"Symbol:{symbol} | TRADE: {trade_direction}"])
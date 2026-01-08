# analysis_runner.py
import asyncio
from collections import deque
from datetime import datetime
from botutils.candlehandling import update_candle_status_all_timeframes,update_candle_open_prices,populate_candle_prices
from asyncio import TimeoutError, wait_for
from botutils.status import status_messages
from botutils import runtimeglobals 
import traceback
import ssl
import certifi
import json
from websockets import connect
#import runtimeglobals
from botutils.place_trade import place_trade
from botutils.analyzer import one_tick_entry
from botutils.martingale import martingale


candle_tasks_started = set()


candle_open_prices = {
    symbol: {tf: None for tf in runtimeglobals.timeframes}
    for symbol in runtimeglobals.MARKETS
}

candle_high_prices = {
    symbol: {tf: None for tf in runtimeglobals.timeframes}
    for symbol in runtimeglobals.MARKETS
}

candle_low_prices = {
    symbol: {tf: None for tf in runtimeglobals.timeframes}
    for symbol in runtimeglobals.MARKETS
}

GRANULARITY_BASE = {
    "1min": 60,
    "5min": 300,
    "15min": 900,
    "30min": 1800,
    "1hr": 3600,
    "4hr": 14400,
}

# Build GRANULARITY_MAP with keys like "candles_1min"
GRANULARITY_MAP = {
    f"candles_{tf}": GRANULARITY_BASE[tf]
    for tf in [tf for tf in runtimeglobals.timeframes if tf != "tick"]

}


running_tasks = set()

def tracked_create_task(coro):
    task = asyncio.create_task(coro)
    running_tasks.add(task)
    task.add_done_callback(lambda t: running_tasks.discard(t))
    return task

async def handle_tick(message, symbol,stop_event):

    tick_data = message.get("tick", {})
    quote = tick_data.get("quote")
    if not symbol or quote is None:
        return

    tick = {
        "symbol": symbol,
        "epoch": tick_data.get("epoch"),
        "quote": float(quote),
        "bid": float(tick_data.get("bid", 0)),
        "ask": float(tick_data.get("ask", 0))
    }

    runtimeglobals.market_data[symbol]["tick_data"].append(tick)
    print("received tick:",symbol ,tick["quote"])
    
    status_messages["ticks"][f"tick_{symbol}"] = tick
    update_candle_open_prices(symbol, runtimeglobals.market_data, candle_open_prices)
    if symbol not in candle_tasks_started:
        tracked_create_task(update_candle_status_all_timeframes(symbol,runtimeglobals.market_data,[tf for tf in runtimeglobals.timeframes if tf != "tick"],stop_event,candle_open_prices, status_messages))

        candle_tasks_started.add(symbol)
    if not runtimeglobals.active_trade:
        await one_tick_entry(symbol,stop_event)
    




async def periodic_heartbeat():
    while True:
        status_messages["heartbeat"] = "💓 still alive"
        #send_telegram_message("💓 still alive")
        await asyncio.sleep(1)


async def fetch_initial_data_with_ws(max_retries=3, delay=10):
    ws = runtimeglobals.ws
    runtimeglobals.active_trade = False

    for symbol in runtimeglobals.MARKETS:
        status_messages["INIT"] = f"\n[INIT] Fetching historical data for {symbol}"
        print(f"\n[INIT] Fetching historical data for {symbol}")
        success_candles = set()
        success_ticks = False
        

        for attempt in range(1, max_retries + 1):
            print(f"  [Attempt {attempt}]")
            status_messages["INIT"] = f"  [Attempt {attempt}]"

            # --- Fetch candles for each timeframe ---
            for tf in [tf for tf in runtimeglobals.timeframes if tf != "tick"]:
                tf_key = f"candles_{tf}"
                if tf_key in success_candles:
                    continue  # Skip if already succeeded

                granularity = GRANULARITY_BASE[tf]
                try:
                    await ws.send(json.dumps({
                        "ticks_history": symbol,
                        "granularity": granularity,
                        "count": 1000,
                        "end": "latest",
                        "style": "candles"
                    }))

                    raw_response = await ws.recv()
                    response = json.loads(raw_response)

                    candles = response.get("candles", [])
                    if candles:
                        runtimeglobals.market_data[symbol][tf_key].extendleft(reversed(candles))
                        success_candles.add(tf_key)
                        status_messages["INIT"] = f"    ✅ {tf_key}: {len(candles)} candles"
                        print(f"    ✅ {tf_key}: {len(candles)} candles")
                    else:
                        status_messages["INIT"] = f"    ⚠️  No candles for {symbol}-{tf_key} (empty response)"
                        print(f"    ⚠️  No candles for {symbol}-{tf_key} (empty response)")

                except Exception as e:
                    status_messages["INIT"] = f"    ❌ Error fetching {tf_key}: {e}"
                    print(f"    ❌ Error fetching {tf_key}: {e}")
                    traceback.print_exc()

                await asyncio.sleep(0.3)  # minor throttle

            # --- Fetch historical ticks ---
            if not success_ticks:
                try:
                    await ws.send(json.dumps({
                        "ticks_history": symbol,
                        "style": "ticks",
                        "count": 5000,
                        "end": "latest"
                    }))

                    raw_tick_response = await ws.recv()
                    tick_response = json.loads(raw_tick_response)

                    if "history" in tick_response and tick_response["history"].get("prices"):
                        prices = tick_response["history"]["prices"]
                        times = tick_response["history"]["times"]
                        pip_size = tick_response.get("pip_size", 2)

                        ticks = [
                            {
                                "quote": price,
                                "quote_str": f"{price:.{pip_size}f}",
                                "epoch": epoch
                            }
                            for price, epoch in zip(prices, times)
                        ]

                        runtimeglobals.market_data[symbol]["tick_data"].extendleft(reversed(ticks))
                        success_ticks = True
                        status_messages["INIT"] = f"    ✅ tick_data: {len(ticks)} ticks"
                        print(f"    ✅ tick_data: {len(ticks)} ticks")
                    else:
                        status_messages["INIT"] = f"    ⚠️  No tick data returned for {symbol}"
                        print(f"    ⚠️  No tick data returned for {symbol}")

                except Exception as e:
                    status_messages["INIT"] = f"    ❌ Error fetching tick_data: {e}"
                    print(f"    ❌ Error fetching tick_data: {e}")
                    traceback.print_exc()

                await asyncio.sleep(0.3)

            # ✅ Exit if everything succeeded
            if success_ticks and len(success_candles) == len(runtimeglobals.timeframes)-1:
                break

            print(f"  ⏳ Retry in {delay}s for remaining...")
            status_messages["INIT"] = f"  ⏳ Retry in {delay}s for remaining..."
            await asyncio.sleep(delay)

        # Final summary per symbol
        status_messages["INIT"] = f"  ▶️  Final status for {symbol}:"
        print(f"  ▶️  Final status for {symbol}:")
        for tf in [tf for tf in runtimeglobals.timeframes if tf != "tick"]:
            tf_key = f"candles_{tf}"
            if tf_key in success_candles:
                status_messages["INIT"] = f"     ✅ {tf_key}"
                print(f"     ✅ {tf_key}")
            else:
                status_messages["INIT"] = f"     ❌ {tf_key} missing"
                print(f"     ❌ {tf_key} missing")

        if success_ticks:
            status_messages["INIT"] = "     ✅ tick_data"
            print("     ✅ tick_data")
        else:
            status_messages["INIT"] = "     ❌ tick_data missing"
            print("     ❌ tick_data missing")



async def send_message(ws, message):
    await ws.send(json.dumps(message))
    return json.loads(await ws.recv())


async def keep_alive(ws):
    while True:
        try:
            await ws.send(json.dumps({"ping": 1}))
        except:
            break
        await asyncio.sleep(30)

async def subscribe_ticks(ws, symbol):
    # Step 1: Send subscription request
    sub_msg = {"ticks": symbol, "subscribe": 1}
    await ws.send(json.dumps(sub_msg))
    print(f"📡 Sent subscription request for {symbol}")

    # Step 2: Receive and parse the response
    response = await ws.recv()
    parsed_message = json.loads(response)

    #print(f"📩 Received subscription response for {symbol}")
    #print("Raw:", response)
    #print("Parsed:", parsed_message)
    
async def subscribe_to_contract_updates(ws, contract_id):
    try:
        await ws.send(json.dumps({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1
        }))
        print(f"[TRACK] Subscribed to updates for contract {contract_id}")
    except Exception as e:
        print(f"❌ Failed to subscribe to contract {contract_id}: {e}")
        traceback.print_exc()


async def handle_contract_update(contract_id, poc,symbol):
    if "tick_entries" not in status_messages:
        status_messages["tick_entries"] = {}
        status_messages["errors"] = {}
        status_messages["profit_loss"] = {}
    try:
        #print(poc)
        profit = poc.get("profit", 0)
        is_expired = poc.get("is_expired", False)
        is_sold = poc.get("is_sold", False)
        status = poc.get("status")
        entry = poc.get("entry_spot","?")
        current = poc.get("current_spot","?")

        print(f"[UPDATE] Contract {contract_id},{symbol}: profit={profit}, entry={entry}, current={current}, status={status}")
        status_messages["tick_entries"]["tracker"] = (
    f"{symbol}"
    f"| Entry: {entry} | Current: {current} | Exit: {current} | Tick P/L: {profit}"
)

        if is_expired or is_sold:
            print(f"✅ Contract {contract_id} complete. Final profit: {profit}")
            
            runtimeglobals.active_trade = False
            runtimeglobals.total_trades += 1
            runtimeglobals.total_profit += profit
            if profit > 0:
                    runtimeglobals.total_wins += 1
                    runtimeglobals.current_loss_streak = 0
            else:
                    runtimeglobals.current_loss_streak += 1
                    runtimeglobals.max_loss_streak = max(runtimeglobals.max_loss_streak, runtimeglobals.current_loss_streak)
                    
            current_stake, _ = martingale(profit, profit > 0, runtimeglobals.martingale_type)
            
            status_messages["profit_loss"]["winstats"] = f"Total Wins:{runtimeglobals.total_wins} | Total Trades:{runtimeglobals.total_trades} | Total P/L:{runtimeglobals.total_profit:.2f} | Current Stake:{runtimeglobals.current_stake:.2f} | Max Loss Streak:{runtimeglobals.max_loss_streak}"
            
                
                

    except Exception as e:
        print(f"⚠️ Error handling contract update for {contract_id}: {e}")
        traceback.print_exc()


async def start_pure_websocket_session(stop_event):
    print("initial stake check",runtimeglobals.initial_stake)
    DERIV_API_URL = f"wss://ws.binaryws.com/websockets/v3?app_id={runtimeglobals.app_id}"
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    tracked_contracts = {}  # contract_id -> status
    active_symbol = None

    while not stop_event.is_set():
        try:
            print("[WS] Connecting to Deriv WebSocket...")
            async with connect(DERIV_API_URL, ssl=ssl_context) as ws:
                runtimeglobals.ws = ws
                if "connection" not in status_messages :
                    status_messages["connection"] = {}
                    status_messages["authorization"] = {}
                    status_messages["trades"] = {}
                print("[WS] ✅ Connected")
                status_messages["connection"]["status"] = "connected"

                # === Authorize ===
                try:
                    await send_message(ws, {"authorize": runtimeglobals.API_token})  # Replace with actual token
                    print("✅ Authorized")
                    status_messages["authorization"]["status"] = "authorized"
                except Exception as e:
                    print(f"❌ Authorization failed: {e}")
                    traceback.print_exc()
                    continue  # Skip this connection session

                
                # === Initial Fetch ===
                
                try:
                    await fetch_initial_data_with_ws()
                    populate_candle_prices(runtimeglobals.market_data, candle_open_prices, candle_high_prices, candle_low_prices, runtimeglobals.timeframes)
                except Exception as e:
                    print(f"❌ Error during initial fetch: {e}")
                    traceback.print_exc()
                

                # === Subscribe to Ticks ===
                try:
                    for symbol in runtimeglobals.MARKETS:
                        await subscribe_ticks(ws, symbol)
                except Exception as e:
                    print(f"❌ Error during tick subscription: {e}")
                    traceback.print_exc()

                # === Keep-Alive ===
                try:
                    asyncio.create_task(keep_alive(ws))
                except Exception as e:
                    print(f"⚠️ Failed to start keep-alive: {e}")
                    traceback.print_exc()

                # === Message Loop ===
                try:
                    while not stop_event.is_set():
                        try:
                            raw_msg = await ws.recv()
                            msg = json.loads(raw_msg)

                            # === Handle Tick Messages ===
                            if "tick" in msg:
                                symbol = msg["tick"].get("symbol")
                                if symbol:
                                    await handle_tick(msg, symbol,stop_event)

                            # === Handle Buy Confirmation ===
                            elif "buy" in msg:
                                contract_id = msg["buy"]["contract_id"]
                                symbol = msg["echo_req"]["parameters"]["symbol"]
                                active_symbol = symbol
                                status_messages["trades"]["trade_update"] = f"[{symbol} TRADE] ✅ Trade executed: {contract_id}"
                                print(f"[DEBUG] Trade request sent successfully. Contract ID: {contract_id},{symbol}")
                                tracked_contracts[contract_id] = {"symbol": symbol, "completed": False}

                                # Subscribe to contract updates (without calling .recv again)
                                await subscribe_to_contract_updates(ws, contract_id)

                            # === Handle Contract Updates ===
                            elif "proposal_open_contract" in msg:
                                poc = msg["proposal_open_contract"]
                                contract_id = poc.get("contract_id")

                                if contract_id in tracked_contracts:
                                    tracked = tracked_contracts[contract_id]
                                    if not tracked["completed"]:
                                        await handle_contract_update(contract_id, poc, tracked["symbol"])
                                        # Mark as completed if expired/sold
                                        if poc.get("is_expired") or poc.get("is_sold"):
                                            tracked_contracts[contract_id]["completed"] = True

                        except Exception as recv_error:
                            print(f"⚠️ Error receiving/parsing message: {recv_error}")
                            traceback.print_exc()
                            break  # Restart connection

                except Exception as fatal_loop_error:
                    print(f"❌ Fatal loop error: {fatal_loop_error}")
                    traceback.print_exc()

        except Exception as outer:
            print(f"❌ WebSocket exception (outer): {outer}")
            traceback.print_exc()

        print("🔁 Reconnecting in 5s...")
        await asyncio.sleep(5)

"""

if __name__ == "__main__":
    import signal

    async def main():
        stop_event = asyncio.Event()

        def handle_exit(*args):
            print("🛑 Stopping...")
            stop_event.set()

        # Handle Ctrl+C or kill signals
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)

        await start_pure_websocket_session(stop_event)

    asyncio.run(main())
    """



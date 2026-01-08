from botutils import runtimeglobals 
from botutils.status import status_messages
import json

barrier_levels = {
    "R_25": 0.19,
    "R_50": 0.023,
    "R_75": 25.7,
    "R_100":0.37,
    "1HZ25V":50.74,
    "1HZ50V":35.12,
    "1HZ75V":1.41,
    "1HZ100V":0.21,
    
}

async def place_trade(symbol, direction):
    print("current stake check",runtimeglobals.current_stake)
    
    #print(f"\n[DEBUG] {symbol}: place_trade() called for {direction}.")
    if "trades" not in status_messages:
        status_messages["trades"] = {}


    # Ensure WebSocket is connected
    if runtimeglobals.ws is None or not runtimeglobals.ws.open:
        print(f"[{symbol} ERROR] WebSocket is not connected. Reconnecting...")
        return

    
    barrier = barrier_levels.get(symbol, 1.0)
    barrier = f"+{barrier}" if direction == "PUT" else f"-{barrier}"
 

    # Prepare trade parameters
    trade_params = {
        "buy": 1,
        "price": runtimeglobals.current_stake,
        "parameters": {
            "amount": runtimeglobals.current_stake,
            "basis": "stake",
            "contract_type": direction,
            "currency": "USD",
            "duration": runtimeglobals.duration,# 5
            "duration_unit": runtimeglobals.duration_unit, #"t"
            "symbol": symbol,
            "barrier": barrier,
        }
    }

    #print(f"[DEBUG] {symbol}: Preparing to send trade request: {json.dumps(trade_params, indent=2)}")

    # Send trade request
    try:
        if runtimeglobals.ws and runtimeglobals.ws.open:
            await runtimeglobals.ws.send(json.dumps(trade_params))
            


            # ✅ Fix: Log time tracking after sending
            
            runtimeglobals.active_trade = True
        else:
            print(f"[{symbol} ERROR] WebSocket not open, trade not sent.")
            runtimeglobals.active_trade = False  # Reset active trade if sending fails

    except Exception as e:
        print(f"[{symbol} TRADE ERROR] Exception while sending trade request: {e}")
        runtimeglobals.active_trade = False  # Reset active trade if error occurs

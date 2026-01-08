from botutils import runtimeglobals 
from botutils.status import status_messages
import asyncio

async def track_trade(api, contract_id, symbol):
    if "tick_entries" not in status_messages:
        status_messages["tick_entries"] = {}
        status_messages["errors"] = {}
        status_messages["profit_loss"] = {}
   
    while runtimeglobals.active_trade:
        await asyncio.sleep(1.5)
        
        
        try:
            response = await api.send({
                "proposal_open_contract": 1,
                "contract_id": contract_id
            })

            #print("\n=== Full Raw Response ===")
            #print(json.dumps(response, indent=2))

            if "proposal_open_contract" not in response:
                print(f"[{symbol} ERROR] No contract in response.")
                continue

            contract = response["proposal_open_contract"]

            # Diagnostic prints
            #print(f"Keys in contract: {list(contract.keys())}")
            #print(f"audit_details: {contract.get('audit_details')}")
            #print(f"is_sold: {contract.get('is_sold')}")
            #print(f"profit: {contract.get('profit')}")

            entry = contract.get("entry_tick", "?")
            current = contract.get("current_spot")
            exit = contract.get("exit_tick", "?")
            profit = float(contract.get("profit", 0.0))

            runtimeglobals.tick_counter[symbol] = runtimeglobals.tick_counter.get(symbol, 0) + 1
            status_messages["tick_entries"]["tracker"] = (
    f"{symbol}, tick_counter: {runtimeglobals.tick_counter[symbol]} "
    f"| Entry: {entry} | Current: {current} | Exit: {exit} | Tick P/L: {profit}"
)

            
            
            # Only balance update if audit details exist
            if contract.get('is_sold') == 1 :

                runtimeglobals.active_trade = False
                runtimeglobals.tick_counter[symbol] = 0

                runtimeglobals.total_trades += 1
                runtimeglobals.total_profit += profit
                if profit > 0:
                    runtimeglobals.total_wins += 1
                    runtimeglobals.current_loss_streak = 0
                else:
                    runtimeglobals.current_loss_streak += 1
                    runtimeglobals.max_loss_streak = max(runtimeglobals.max_loss_streak, runtimeglobals.current_loss_streak)

                
                status_messages["profit_loss"]["winstats"] = f"Total Wins:{runtimeglobals.total_wins} | Total Trades:{runtimeglobals.total_trades} | Total P/L:{runtimeglobals.total_profit:.2f} | Current Stake:{runtimeglobals.current_stake:.2f} | Max Loss Streak:{runtimeglobals.max_loss_streak}"
                break

        except Exception as e:
            status_messages["errors"]["track_trade"] = f"[ERROR] Failed to fetch contract update: {e}"

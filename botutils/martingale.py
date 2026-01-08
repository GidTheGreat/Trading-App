from botutils import runtimeglobals

def martingale(profit_value, last_trade_was_win, mode=runtimeglobals.martingale_type):
    

    if mode == "mode_3factor":
        if last_trade_was_win:
            runtimeglobals.win_streak += 1
            if win_streak < runtimeglobals.martingale_multiplier:  
                if profit_value > 0:  
                    runtimeglobals.current_stake += profit_value  
            else:  
                runtimeglobals.current_stake = runtimeglobals.initial_stake  
                runtimeglobals.win_streak = 0  
        else:
            runtimeglobals.current_stake = runtimeglobals.initial_stake  
            runtimeglobals.win_streak = 0  

    elif mode == "mode_x2":
        if last_trade_was_win:
            runtimeglobals.current_stake = runtimeglobals.initial_stake  
            runtimeglobals.win_streak = 0
        else:
            runtimeglobals.current_stake *=runtimeglobals.martingale_multiplier
            

    

    elif mode == "mode_x23factor":
        if last_trade_was_win:
            runtimeglobals.win_streak += 1
            if runtimeglobals.win_streak < 3:  
                if profit_value > 0:  
                    runtimeglobals.current_stake += profit_value  
            else:  
                runtimeglobals.current_stake = runtimeglobals.initial_stake  
                runtimeglobals.win_streak = 0  
        else:
            runtimeglobals.current_stake = runtimeglobals.initial_stake
            runtimeglobals.current_stake *= runtimeglobals.martingale_multiplier  # ✅ Triple stake on loss
            runtimeglobals.win_streak = 0  

    

    return runtimeglobals.current_stake, runtimeglobals.win_streak 
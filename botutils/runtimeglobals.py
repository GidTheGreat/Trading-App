#runtimeglobals
from collections import deque

run_mode = "Local"

app_id = None
active_trade = False
balance = 0.0
payout = 0.0
initial_stake = None
martingale_type = None
win_streak = 0  

contract_type = ''
total_wins = 0
total_trades = 0
total_profit = 0.0
current_loss_streak = 0
max_loss_streak = 0
active_trades = {}
tick_counter = {}



timeframes = ["tick"]

MARKETS = []

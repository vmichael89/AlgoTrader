import os
os.chdir("../trader")
from trader.trader import Trader
from trader.strategies.continuation_strat import Strategy


trader = Trader()
trader.add_broker('mt5')
trader.add_strategy(Strategy(instrument='EURUSD', frequency=1))
trader.add_strategy(Strategy(instrument='EURUSD', frequency=1))

print(trader.strategies[0].criteria_manger.criteria[0].dc_indicator == trader.strategies[1].criteria_manger.criteria[0].dc_indicator)

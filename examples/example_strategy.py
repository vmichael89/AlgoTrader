import os
os.chdir("../trader")
from trader.trader import Trader
from trader.strategies import ContinuationStrategy


trader = Trader()
trader.add_broker('mt5')
trader.add_strategy(ContinuationStrategy(instrument='EURUSD', frequency=1))
trader.run_live()

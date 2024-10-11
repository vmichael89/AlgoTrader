import os
os.chdir("../trader")
from trader.trader import Trader

trader = Trader('polygon')
trader.add_data(instruments = 'C:EURUSD', granularities=['1H', '1M'])
# trader.save_data(save_all=True)
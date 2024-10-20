import os
os.chdir("../trader")
from trader.trader import Trader

trader = Trader()
trader.add_broker('polygon')
trader.add_data(instruments='C:EURUSD', granularities=['1H', '1D'])
trader.add_broker('oanda')
trader.add_data(instruments='EUR_USD', granularities=['1H', '1D'], broker='oanda')

# plot oanda and polygon data together
trader.plot_bid_ask_candles(0, 2, equal_instruments=False)

# trader.save_data(save_all=True)
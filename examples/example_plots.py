import os
os.chdir("../trader")
from trader.trader import Trader

trader = Trader()
trader.add_broker('oanda')
trader.add_data(['EUR_USD'], granularities="1H")
trader.add_data(['EUR_USD'], granularities="1D")
trader.plot_dual_timeframe(0, 1)


trader = Trader()
trader.add_broker('oanda')
trader.add_data(['EUR_USD'], prices=['B', 'A'])
trader.plot_bid_ask_candles(0, 1)

trader.data[0].plot()

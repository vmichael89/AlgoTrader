import os
os.chdir("../trader")
from trader.trader import Trader

trader = Trader()
trader.add_data(['EUR_USD'], granularity="H1")
trader.add_data(['EUR_USD'], granularity="D")
trader.plot_dual_timeframe(0, 1)


trader = Trader()
trader.add_data(['EUR_USD'], price="BA")
trader.plot_bid_ask_candles(0, 1)

trader.data[0].plot()

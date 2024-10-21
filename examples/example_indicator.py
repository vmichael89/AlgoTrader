import os
import pandas_ta as ta
os.chdir("../trader")
from trader.trader import Trader

trader = Trader()
trader.add_broker('oanda')
trader.add_data(instruments='EUR_USD', granularities='15min')

# add indicator from ta-lib (see ta.Category for which indicators are available)
trader.add_indicator(indicator='sma', length=10)

# plot
trader.data[0].plot()

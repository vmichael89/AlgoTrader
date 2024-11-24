import os
import pandas_ta as ta
os.chdir("../trader")
from trader.trader import Trader

trader = Trader()
trader.add_broker('oanda')
trader.add_data(instruments='EUR_USD', granularities='1min', start='2024-11-08')

# add indicator from ta-lib (see ta.Category for which indicators are available)
# trader.add_indicator('bbands')
#
trader.add_indicator(indicator='dc', sigma=0.001)

# trader.add_indicator('rsi', length=100)
# trader.data[0].df['RSI_100_'] = trader.data[0].df['RSI_100']/100*(trader.data[0].df.high.max() - trader.data[0].df.low.min()) + trader.data[0].df.low.min()
df = trader.data[0].df
df['min'] = df.low.min()
df['max'] = df.high.max()
# df['event'] = (df['DC_extreme'] > 0).diff() * (trader.data[0].df.high.max() - trader.data[0].df.low.min()) + trader.data[0].df.low.min()
# trader.add_indicator('sma', length=100)

# plot
trader.data[0].plot(renderer='browser')

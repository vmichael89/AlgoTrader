import os
os.chdir("..")
from trader.trader import Trader
from trader.indicators.support_resistance_levels import SupportResistance
import trader.indicators.trading_session as ts

trader = Trader()
trader.add_broker("mt5")

# data
trader.add_data("EURUSD", granularities="tick")
fig = trader.plot()[0]

# s/r levels
sr = SupportResistance(trader.data[0], high_colname="bid", low_colname="bid")
sr.time_based_levels()
for obj in sr.plot_obj():
    fig.add_trace(obj)

# sessions
df_sessions = ts.get_sessions(trader.data[0].df)
fig = ts.plot_sessions(df_sessions, fig)

# news

fig.show(renderer="browser")
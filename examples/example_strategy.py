import os
os.chdir("../trader")
from trader.trader import Trader
from trader.strategies import ContinuationStrategy

from plotly import graph_objects as go


trader = Trader()
trader.add_broker('mt5')
trader.add_strategy(ContinuationStrategy(instrument='EURUSD', frequency=1, sigma=0.0001))
# trader.run_live()
trader.run_backtest(start="2025-01-03T10:00+02:00", end="2025-01-03T20:00+02:00")


# Analysis

print(*trader.strategies[0].criteria_manger.met_criteria, sep='\n')

[fig] = trader.plot()
dc = trader.indicators[0]
fig.add_trace(go.Scatter(x=dc.extremes.index, y=dc.extremes['extreme'], mode='lines', name='Extreme'))

data = trader.data[0].df.bid
for chain in trader.strategies[0].criteria_manger.met_criteria:
    timestamps = [ts for ts in chain if ts]
    values = [data[ts] for ts in timestamps]
    fig.add_trace(go.Scatter(x=timestamps, y=values, mode='markers+lines', marker_color='black' if len(timestamps) == 3 else 'red'))

fig.update_layout(showlegend=False).show(renderer='browser')

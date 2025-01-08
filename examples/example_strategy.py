import os
os.chdir("../trader")
from trader.trader import Trader
from trader.strategies import ContinuationStrategy

from plotly import graph_objects as go


trader = Trader()
trader.add_broker('mt5')
strat = ContinuationStrategy(instrument='EURUSD', frequency=1, sigma=0.0001, max_retracement=0.5, allow_new_extremes=True)
trader.add_strategy(strat)
# trader.run_live()

trader.run_backtest(start="2025-01-03T10:00+02:00", end="2025-01-03T20:00+02:00")


# Analysis

print(*trader.strategies[0].criteria_manger.met_criteria, sep='\n')

# Plot price
[fig] = trader.plot()

# Plot zigzag
dc = trader.indicators[0]
fig.add_trace(go.Scatter(x=dc.extremes.index, y=dc.extremes['extreme'], mode='lines', name='Extreme'))

# Plot criteria
data = trader.data[0].df.bid
for chain in trader.strategies[0].criteria_manger.met_criteria:
    # Remove False values
    conf_timestamps = [ts for ts in chain if ts]
    # Extreme criteria save the timestamp of the confirmation
    # Get the timestamps of the extremes (only the first 2 entries are Extreme criteria)
    timestamps = [dc.extremes[dc.extremes['conf_time'] == ts].index[0] if i<1 else ts for i, ts in enumerate(conf_timestamps)]
    # timestamps = conf_timestamps
    values = [data[ts] for ts in timestamps]
    fig.add_trace(go.Scatter(x=timestamps, y=values, mode='markers+lines', marker_color='black' if len(timestamps) == 3 else 'red'))
for crit in trader.strategies[0].criteria_manger.criteria[1:]:
    for plot_obj in crit.plot_objects():
        fig.add_trace(plot_obj)
# Set title to the settings of the strat set in the beginning
fig.update_layout(title="\n".join([strat.name, str(strat.sigma), str(strat.max_retracement), str(strat.allow_new_extremes)]), xaxis_title='Time', yaxis_title='Price')

fig.update_layout(showlegend=False).show(renderer='browser')

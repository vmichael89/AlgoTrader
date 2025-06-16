from datetime import datetime
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import os
os.chdir("..")
from trader.trader import Trader


trader = Trader()
trader.add_broker("mt5")

start_date = "2024-04-01"

# create 4 weeks of data
for i in range(4):
    end_date = datetime.strptime(start_date, "%Y-%m-%d") + pd.DateOffset(days=6)
    trader.add_data("EURUSD", start=start_date, end=end_date.strftime("%Y-%m-%d"), granularities="1H")
    start_date = (end_date + pd.DateOffset(days=1)).strftime("%Y-%m-%d")

df = trader.data[0].df

# Create subplots
fig = make_subplots(rows=4, cols=1, shared_xaxes=True)

# Add traces for each week
for i, week_data in enumerate(trader.data):
    week_df =  week_data.df

    fig.add_trace(go.Scattergl(
        x=week_df.index,
        y=week_df.bid,
        mode='lines+markers',
    ), row=i + 1, col=1)

    # Set x-axis range to Monday - Sunday for each subplot
    # fig.update_xaxes(range=[week_start, week_end], row=i + 1, col=1)


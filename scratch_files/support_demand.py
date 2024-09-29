import os
import datetime
import plotly.graph_objs as go
import pandas_ta as ta
os.chdir("..")
from trader.algos.directional_change import DirectionalChange
from trader.trader import Trader
os.chdir("trader")

trader = Trader()

days = 60
days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).date().strftime('%Y-%m-%d')
trader.add_data(['EUR_USD'], start=days_ago, granularity='M15')


data = trader.data[0]
df = data.df

dc = DirectionalChange(0.0015).get_extremes(df)

fig = go.Figure(data=[go.Candlestick(x=df.index, open=df.open, high=df.high, low=df.low, close=df.close)])
fig.update_layout(title=str(data), xaxis_rangeslider_visible=False)
fig.add_scatter(x=dc.extremes.index, y=dc.extremes.extreme)
fig.show(renderer='browser')

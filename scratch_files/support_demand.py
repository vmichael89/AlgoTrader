import os
import datetime
import plotly.graph_objs as go
os.chdir("..")
from trader.algos.directional_change import DirectionalChange
from trader.trader import Trader
os.chdir("trader")

trader = Trader()

days = 60
days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).date().strftime('%Y-%m-%d')
trader.add_data(['EUR_USD'], start=days_ago, granularity='M15')

dc = DirectionalChange(0.0015).get_extremes(trader.data[0].df)
df = dc.extremes.copy()

bottoms = df[df.type == 'bottom']  # shortcut
# new column indication higher highs
df['higher_bottom'] = (bottoms.extreme > bottoms.extreme.shift(1)).astype(int)
# new column counting consecutive higher highs
df['higher_bottom_count'] = df['higher_bottom'].groupby((df['higher_bottom'] == 0).cumsum()).cumsum()

tops = dc.extremes[dc.extremes.type == 'top']  # shortcut
df['higher_top'] = (tops.extreme > tops.extreme.shift(1)).astype(int)
df['higher_top_count'] = df['higher_top'].groupby((df['higher_top'] == 0).cumsum()).cumsum()

# inspect dataframe step by step
df.drop(columns=['higher_bottom', 'higher_top'], inplace=True)
df.ffill(inplace=True)
df.bfill(inplace=True)

# merge extremes wit data
df = trader.data[0].df.merge(df, left_index=True, right_index=True, how='outer')

# plot
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df.open, high=df.high, low=df.low, close=df.close)])
fig.update_layout(title=str(trader.data[0]), xaxis_rangeslider_visible=False)
fig.add_scatter(x=dc.extremes.index, y=dc.extremes.extreme)

# Add annotations for higher bottom counts
for i, row in df[df['type'] == 'bottom'].iterrows():
    fig.add_annotation(
        x=i,
        y=row['extreme'],
        text=f"{int(row['higher_bottom_count'])}",
        showarrow=False,
        bgcolor="lightblue"
    )

# Add annotations for higher top counts
for i, row in df[df['type'] == 'top'].iterrows():
    fig.add_annotation(
        x=i,
        y=row['extreme'],
        text=f"{int(row['higher_top_count'])}",
        showarrow=False,
        bgcolor="lightgreen"
    )

fig.show(renderer='browser')

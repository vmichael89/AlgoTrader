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


# PLOT

# plot candle chart
fig = go.Figure(data=[go.Candlestick(x=df.index, open=df.open, high=df.high, low=df.low, close=df.close)])
fig.update_layout(title=str(trader.data[0]), xaxis_rangeslider_visible=False)

# plot extremes
fig.add_scatter(x=dc.extremes.index, y=dc.extremes.extreme, line_color='black', opacity=0.5)

# plot annotations for higher bottom counts
for i, row in df[df['type'] == 'bottom'].iterrows():
    fig.add_annotation(
        x=i,
        y=row['extreme'],
        text=f"{int(row['higher_bottom_count'])}",
        showarrow=False,
        bgcolor="lightblue"
    )

# plot annotations for higher top counts
for i, row in df[df['type'] == 'top'].iterrows():
    fig.add_annotation(
        x=i,
        y=row['extreme'],
        text=f"{int(row['higher_top_count'])}",
        showarrow=False,
        bgcolor="lightgreen"
    )

# get timestamps of specific number of consecutive higher high/low counts
last_extremes_gr_thresh = [None, None]
type_names = ('bottom', 'top')
count_names = ['higher_bottom_count', 'higher_top_count']
count_threshold = 3
relevant_extremes = []

for timestamp, row in df[['type', 'higher_bottom_count', 'higher_top_count']].dropna().iterrows():
    # keep track of last extremes of which count is higher than the threshold
    for itype in range(2):
        if row['type'] == type_names[itype]:
            if row[count_names[itype]] >= count_threshold:
                last_extremes_gr_thresh[itype] = timestamp
    # if both high and and low pass the condition, add timestamps to list
    if (row[count_names] >= count_threshold).all():
        relevant_extremes.extend(last_extremes_gr_thresh)

relevant_extremes = list(set(relevant_extremes))  # sort and remove duplicates

# plot the actual markers
fig.add_scatter(
    x=relevant_extremes,
    y=dc.extremes.extreme[relevant_extremes],
    mode='markers',
    marker_symbol='circle-open',
    marker_color='black',
    marker_size=30
)

# Update x-axis to hide weekends
fig.update_xaxes(
    rangebreaks=[
        dict(bounds=["sat", "mon"])
    ]
)

fig.show(renderer='browser')

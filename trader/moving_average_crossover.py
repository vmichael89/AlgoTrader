from algos.trendline_automation import fit_trendlines_single
import pandas_ta as ta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from algos.directional_change import DirectionalChange
from broker import PolygonAPI
import itertools
import seaborn as sns


def moving_average_crossover(
        ohlcv: pd.DataFrame, fast_ma_length: int,
        slow_ma_length: int
):
    close = ohlcv['close'].map(np.log)

    fast_ma = close.rolling(window=fast_ma_length).mean().to_numpy()
    slow_ma = close.rolling(window=slow_ma_length).mean().to_numpy()

    trades = pd.DataFrame()
    trade_i = 0

    in_trade = False
    plot = False


    for i in range(1, len(ohlcv)):
        if np.isnan(fast_ma[i]) or np.isnan(slow_ma[i]) or np.isnan(fast_ma[i-1]) or np.isnan(slow_ma[i-1]):
            continue

        if fast_ma[i-1]<slow_ma[i-1] and fast_ma[i]>slow_ma[i]:
            if in_trade:
                trades.loc[trade_i, 'exit_p'] = close.iloc[i]
                trades.loc[trade_i, 'exit_i'] = i
                trade_i+=1

                in_trade = False

            in_trade = True
            trades.loc[trade_i, 'type'] = 'long'
            trades.loc[trade_i, 'entry_i'] = i
            trades.loc[trade_i, 'entry_p'] = close.iloc[i]

            plot = True

        if fast_ma[i - 1] > slow_ma[i - 1] and fast_ma[i] < slow_ma[i]:
            if in_trade:
                trades.loc[trade_i, 'exit_p'] = close.iloc[i]
                trades.loc[trade_i, 'exit_i'] = i
                trade_i += 1

                in_trade = False

            in_trade = True
            trades.loc[trade_i, 'type'] = 'short'
            trades.loc[trade_i, 'entry_i'] = i
            trades.loc[trade_i, 'entry_p'] = close.iloc[i]

            plot = True
        #
        # if plot:
        #     plt.plot(close.to_numpy()[:i])
        #     plt.plot(fast_ma[:i])
        #     plt.plot(slow_ma[:i])
        #     plt.show()
        #
        # plot = False

    trades = trades[:-1]

    trades['return'] = np.where(
        trades['type'] == 'long',
        trades['exit_p'] - trades['entry_p'],  # Calculate return for 'long' trades
        trades['entry_p'] - trades['exit_p']  # Calculate return for 'short' trades
    )

    return trades

api = PolygonAPI()
start = '2023-09-21'
end = '2024-09-21'
instruments = ['X:SOLUSD']
granularity = ['1','hour']

data = api.get_data(instruments, start, end, granularity)[instruments[0]]

data['log_return'] = np.log(data['close'] / data['close'].shift(1))
data['cumulative_log_return'] = data['log_return'].cumsum()

trades = moving_average_crossover(data, 20, 70)

equity_curve = pd.Series(index=range(len(trades)), dtype=float).fillna(0)

# Set the initial equity
current_equity = 0

# Update the equity curve based on trades
for index, row in trades.iterrows():
    # Add the return to the current equity
    current_equity += row['return']

    # Update the equity curve at the entry index of the trade
    equity_curve[row['entry_i']] = current_equity

# Forward fill the equity curve to fill gaps
equity_curve = equity_curve.ffill()

data.reset_index(drop=True, inplace=True)

plt.plot(equity_curve)
plt.plot(data['cumulative_log_return'])
plt.show()

#
# fast_range = range(20, 101, 5)  # From 20 to 100, step by 5
# combinations = [(fast, slow) for fast, slow in itertools.combinations(fast_range, 2)]
#
# results = {}
#
# for i, (fast, slow) in enumerate(combinations):
#     print(f'Combination {i+1}/{len(combinations)}')
#
#     trades = moving_average_crossover(data, fast, slow)
#     total_return = trades['return'].sum()
#     results[(fast, slow)] = total_return
#
# heatmap_df = pd.DataFrame(index=fast_range, columns=fast_range)
#
# for (fast, slow), total_return in results.items():
#     heatmap_df.loc[fast, slow] = total_return
#
# heatmap_df = heatmap_df.apply(pd.to_numeric)
#
# plt.figure(figsize=(10, 8))
# sns.heatmap(heatmap_df, cmap="YlGnBu", annot=True, fmt=".1f")
# plt.title("Performance of Moving Average Crossover Strategy")
# plt.xlabel("Slow Moving Average")
# plt.ylabel("Fast Moving Average")
# plt.show()
#
# print(trades['return'].sum())
#
# log_data = data.map(np.log)
# print(log_data['close'].iloc[-1] - log_data['close'].iloc[0])
import os
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt
os.chdir("..")
from trader.algos.directional_change import DirectionalChange
from trader.broker import PolygonAPI
os.chdir("trader")
import json
from trader.trader import Trader
import datetime

# Define the main function
def directional_trades(ohlcv: pd.DataFrame, lookback: int = 250, atr_lookback: int = 100, hold_period = 48,
                                     tp_mult : float=3.0, sl_mult : float=3.0, plot_graphs : bool = False, sigma : float = 0.0025,
                                     max_tolerance : int = 3, atr_min : float = 0.0010, alpha_1: float = 0.15, alpha_2: float = 0.25, plot_lookback : int = 250):
    ohlcv = ohlcv.reset_index()  # Reset the index

    numeric_cols = ohlcv.select_dtypes(include=[np.number]).columns
    ohlcv[numeric_cols] = np.log(ohlcv[numeric_cols])

    close = ohlcv['close'].to_numpy()

    # Calculate ATR
    atr_arr = ta.atr(ohlcv['high'], ohlcv['low'],ohlcv['close'], atr_lookback)
    atr_arr = atr_arr.to_numpy()

    atr_arr_5 = ta.atr(ohlcv['high'], ohlcv['low'],ohlcv['close'], 5)
    atr_arr_5 = atr_arr_5.to_numpy()

    ma_arr_weekly = ohlcv['close'].rolling(4800).mean()
    # ma_arr_daily = ohlcv['close'].rolling(1200).mean()
    # ma_arr_hourly = ohlcv['close'].rolling(300).mean()
    #
    # ma_arr_weekly = ma_arr_weekly.to_numpy()
    # ma_arr_daily = ma_arr_daily.to_numpy()

    trades = pd.DataFrame()
    trade_i = 0

    consolidation_zones = {}

    in_trade = False
    tp_price = None
    sl_price = None
    hp_i = None

    directional_change = DirectionalChange(sigma=sigma)
    all_extremes = directional_change.get_extremes(ohlcv).extremes
    all_extremes['conf_time'] = all_extremes['conf_time'].astype(int)

    time_in_market = 0

    for i in range(lookback, len(ohlcv)):
        if not in_trade:
            extremes = all_extremes.loc[all_extremes['conf_time'] <= i].copy()

            if len(extremes)<2:
                continue

            extreme_tops = extremes.loc[extremes['type']=='top']
            extreme_bottoms = extremes.loc[extremes['type']=='bottom']

            bottom_limit = (1 - alpha_1) * extremes.iloc[-2]['extreme'] + alpha_1 * extremes.iloc[-1]['extreme']
            top_limit = (1 - alpha_2) * extremes.iloc[-2]['extreme'] + alpha_2 * extremes.iloc[-1]['extreme']

            for j in range(extremes.index[-2] + 3, extremes.index[-1]):
                if abs(close[j] - close[j - 3]) < 0.00025:
                    consolidation_zones[trade_i] = (
                    range(j - 3, j + 1), min(ohlcv['low'][j - 3: j + 1]),
                    max(ohlcv['close'][j - 3: j + 1]))
                    break

            if (extremes.iloc[-1]['extreme'] - extremes.iloc[-2]['extreme']) / (extremes.index[-1] - extremes.index[-2]) > 0.0001 and \
                    extremes.iloc[-1]['type'] == 'top' and extremes.iloc[-2]['type'] == 'bottom' and \
                    close[i] <= top_limit and \
                    np.all((bottom_limit < close[extremes.index[-1]: i + 1]) & (close[extremes.index[-1]: i + 1] < extremes.iloc[-1]['extreme'])) and \
                    (extreme_tops.iloc[-3]['extreme'] <= extreme_tops.iloc[-2]['extreme'] <= extreme_tops.iloc[-1]['extreme']) and \
                    (extreme_bottoms.iloc[-3]['extreme'] <= extreme_bottoms.iloc[-2]['extreme'] <=
                     extreme_bottoms.iloc[-1]['extreme']):

            # if (extremes.iloc[-1]['extreme']- extremes.iloc[-2]['extreme']) / (extremes.index[-1] - extremes.index[-2]) > 0.0001 and \
            #         extremes.iloc[-1]['type'] == 'top' and extremes.iloc[-2]['type'] == 'bottom' and \
            #         close[i] <= top_limit and \
            #         np.all((bottom_limit < close[extremes.index[-1]: i + 1]) & (close[extremes.index[-1]: i + 1] < extremes.iloc[-1]['extreme'])) and \
            #         (extreme_tops.iloc[-3]['extreme'] <= extreme_tops.iloc[-2]['extreme'] <= extreme_tops.iloc[-1][
            #             'extreme']) and \
            #         (extreme_bottoms.iloc[-3]['extreme'] <= extreme_bottoms.iloc[-2]['extreme'] <=
            #          extreme_bottoms.iloc[-1]['extreme']):

                # if extremes.iloc[-1]['type']=='top' and extremes.iloc[-2]['type']=='bottom' and \
            #         bottom_limit <= close[i] <= top_limit and \
            #         (extreme_tops.iloc[-3]['extreme'] <= extreme_tops.iloc[-2]['extreme'] <= extreme_tops.iloc[-1]['extreme']) and \
            #         (extreme_bottoms.iloc[-3]['extreme'] <= extreme_bottoms.iloc[-2]['extreme'] <= extreme_bottoms.iloc[-1]['extreme']):

            # if close[i] >= ma_arr_weekly[i] and \
            #         extremes.iloc[-1]['type'] == 'top' and extremes.iloc[-2]['type'] == 'bottom' and \
            #         close[i] <= top_limit and \
            #         np.all((bottom_limit < close[extremes.index[-1]: i+1]) & (close[extremes.index[-1]: i+1] < extremes.iloc[-1]['extreme'])) and \
            #         (extreme_tops.iloc[-2]['extreme'] <= extreme_tops.iloc[-1]['extreme']) and \
            #         (extreme_bottoms.iloc[-2]['extreme'] <=extreme_bottoms.iloc[-1]['extreme']):
            # #
            # pullback_reversal = extremes.loc[(extremes.index >= i - 10) & (extremes['conf_time'] <= i), 'type']
            #
            # if len(pullback_reversal)!= 0 and \
            #     extremes.iloc[-2]['type'] == 'top' and extremes.iloc[-3]['type'] == 'bottom' and \
            #         bottom_limit <= close[i] <= top_limit and \
            #         np.all(close[extremes.index[-2]: i] > bottom_limit) and \
            #         (extreme_tops.iloc[-3]['extreme'] <= extreme_tops.iloc[-2]['extreme']) and \
            #         (extreme_bottoms.iloc[-3]['extreme'] <= extreme_bottoms.iloc[-2]['extreme']):

                in_trade = True

                trades.loc[trade_i, 'sl'] = extremes.iloc[-2]['extreme']
                trades.loc[trade_i, 'tp'] = extremes.iloc[-1]['extreme']
                trades.loc[trade_i, 'hp_i'] = i + hold_period
                trades.loc[trade_i, 'type'] = 1
                trades.loc[trade_i, 'entry_p'] = close[i]
                trades.loc[trade_i, 'entry_i'] = i

                # print(f"Ratio: {(trades.loc[trade_i, 'tp'] - trades.loc[trade_i, 'entry_p'])/(trades.loc[trade_i, 'entry_p'] - trades.loc[trade_i, 'sl'])}")

        if in_trade:

            time_in_market += 1

            if (trades.loc[trade_i, 'type'] == 1 and (close[i] >= trades.loc[trade_i, 'tp'] or close[i] <= trades.loc[trade_i, 'sl'])) or \
                    (trades.loc[trade_i, 'type'] == 0 and (close[i] <= trades.loc[trade_i, 'tp'] or close[i] >= trades.loc[trade_i, 'sl'])) or \
                    (i >= trades.loc[trade_i, 'hp_i']):
                trades.loc[trade_i, 'exit_i'] = i
                trades.loc[trade_i, 'exit_p'] = close[i]

                if plot_graphs:
                    # Plotting the results
                    plt.figure(figsize=(14, 7))

                    if (trades.loc[trade_i, 'exit_p'] - trades.loc[trade_i, 'entry_p'] > 0 and trades.loc[
                        trade_i, 'type'] == 1) or \
                            (trades.loc[trade_i, 'entry_p'] - trades.loc[trade_i, 'exit_p'] > 0 and trades.loc[
                                trade_i, 'type'] == 0):
                        plt.text(0.5, 1.075, "Success", fontsize=20, fontweight='bold', color='green',
                                 horizontalalignment='center', transform=plt.gca().transAxes)
                    else:
                        plt.text(0.5, 1.075,
                                 "Failure",
                                 fontsize=20, fontweight='bold', color='red', horizontalalignment='center',
                                 transform=plt.gca().transAxes)

                    # Plotting close prices
                    plt.plot(ohlcv['close'].iloc[int(trades.loc[trade_i, 'entry_i']) - plot_lookback:i + 1],
                             label='Close Prices', color='blue', linewidth=2)

                    # Plotting take profit and stop loss levels
                    plt.axhline(y=trades.loc[trade_i, 'tp'], color='green', linestyle='--', label='Take Profit',
                                linewidth=3)
                    plt.axhline(y=trades.loc[trade_i, 'sl'], color='red', linestyle='--', label='Stop Loss',
                                linewidth=3)
                    plt.axvline(x=trades.loc[trade_i, 'entry_i'], color='black', linestyle=':', label='Entry Point',
                                linewidth=2.5)
                    #
                    # print(all_extremes.loc[(all_extremes.index <= i + 1) & (
                    #         all_extremes.index >= int(trades.loc[trade_i, 'entry_i']) - lookback)].copy()['extreme'])

                    # Plotting extremes
                    plt.plot(all_extremes.loc[(all_extremes.index <= i + 1) & (
                            all_extremes.index >= int(trades.loc[trade_i, 'entry_i']) - plot_lookback)].copy()['extreme'],
                             color='purple', label='Extremes', zorder=5, linewidth=2, alpha=0.5)

                    # Plotting high and low prices as a translucent background

                    plt.fill_between(range(int(trades.loc[trade_i, 'entry_i']) - plot_lookback, i + 1),
                                     ohlcv['high'].iloc[int(trades.loc[trade_i, 'entry_i']) - plot_lookback:i + 1],
                                     ohlcv['low'].iloc[int(trades.loc[trade_i, 'entry_i']) - plot_lookback:i + 1],
                                     color='gray', alpha=0.3, label='High-Low Range')

                    if trade_i in consolidation_zones:
                        plt.fill_between(consolidation_zones[trade_i][0], consolidation_zones[trade_i][1],
                                         consolidation_zones[trade_i][2], color='green', alpha=0.3, label='Consolidation Zone')

                    plt.title(
                        f'Support and Resistance Strategy from {ohlcv["date"].iloc[int(trades.loc[trade_i, "entry_i"]) - plot_lookback]} to {ohlcv["date"].iloc[i + 1]}')
                    plt.xlabel('Time Index')
                    plt.ylabel('Price')
                    plt.legend()
                    plt.grid()
                    plt.show()

                in_trade = False
                trade_i += 1
    #
    # print(trades)

    if len(trades) > 0:
        trades['return'] = trades.apply(
            lambda row: row['exit_p'] - row['entry_p'] if row['type'] == 1
            else row['entry_p'] - row['exit_p'],
            axis=1
        )

    # print(trades['return'])

    percent_time_in_market = time_in_market/len(range(lookback, len(ohlcv)))

    return trades, percent_time_in_market

if __name__ == "__main__":
    with open('../data/maven_pairs_oanda.json') as json_file:
        maven_pairs = json.load(json_file)

    instrument = "C:USDJPY"

    start = '2023-09-18'
    end = '2024-09-18'
    granularity = ['10', 'minute']

    # total_win_count = 0
    # total_trade_count = 0
    # all_profit = 0
    # risk_rewards = []
    #
    # for instrument in instruments:
    #     print("Fetching data...")
    #     api = PolygonAPI()
    #     df = api.get_data([instrument], start, end, granularity)[instrument]
    #
    #     print("Running strategy...")
    #     trades = directional_trades(df, plot_graphs=False, sigma=0.0025, atr_min=0, alpha=0.50, hold_period = float('inf'))
    #
    #     # Calculate total profit
    #     total_profit = trades['return'].sum() if len(trades)>0 else 0
    #
    #     # Calculate win rate
    #     win_count = (trades['return'] > 0).sum() if len(trades)>0 else 0
    #     total_trades = len(trades)
    #     # win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
    #
    #     total_win_count += win_count
    #     total_trade_count += total_trades
    #
    #     all_profit += total_profit
    #
    #     risk_reward = trades[trades['return'] > 0]['return'].sum() / abs(trades[trades['return'] < 0]['return'].sum())
    #
    #     risk_rewards.append(risk_reward)
    #
    # win_rate = (total_win_count / total_trade_count) * 100 if total_trade_count > 0 else 0
    # risk_reward = np.mean(risk_rewards)

    for instrument in maven_pairs:
        print(instrument)
        # print("Fetching data...")

        # api = PolygonAPI()
        # df = api.get_data([instrument], start, end, granularity)[instrument]

        api = Trader()
        api.add_data([instrument], start=start, end=end, granularity='M10')
        df = api.data[0].df

        # trader = Trader()
        # days = 60
        # days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).date().strftime('%Y-%m-%d')
        # trader.add_data(['EUR_USD'], start='2023-07-31', granularity='M15')

        # print("Running strategy...")
        trades, percent_time_in_market = directional_trades(df, plot_graphs=False, sigma=0.0005, atr_min=0, alpha_1 = 0,
                                                            alpha_2=0.5, hold_period = float('inf'), plot_lookback = 75)

        # Calculate total profit
        total_profit = trades['return'].sum() if len(trades)>0 else 0

        # Calculate win rate
        win_count = (trades['return'] > 0).sum() if len(trades)>0 else 0
        total_trades = len(trades)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0

        risk_reward = trades[trades['return'] > 0]['return'].mean() / abs(trades[trades['return'] < 0]['return'].mean())

        log_close = np.log(df['close'].to_numpy())
        buy_and_hold = log_close[-1] - log_close[0]

        print(f"Total Profit {total_profit}")
        print(f"Win Rate: {win_rate}")
        print(f'Time in Market: {percent_time_in_market}')
        print(f"Total Trades: {total_trades}")
        print(f"Average R/R Ratio: {risk_reward}")
        print(f"Buy and Hold: {buy_and_hold}")
        print('\n')
        print('\n')

        # # Print the results
        # print(f'Total Profit: {all_profit}')
        # print(f'Win Rate: {win_rate:.2f}%')
        # print(f'Total Trade Count: {total_trade_count}')
        # print(f"Buy and Hold: {buy_and_hold}")
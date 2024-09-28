from algos.directional_change import DirectionalChange
from broker import PolygonAPI
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt

# Define the main function
def support_and_resistance_rejection(ohlcv: pd.DataFrame, lookback: int = 240, atr_lookback: int = 168, hold_period = 48, confirmation_wait:int=12,
                                     tp_mult : float=3.0, sl_mult : float=3.0, plot_graphs : bool = False, sigma : float = 0.0025,
                                     min_bounces : int = 2, zone_size : float = 0.002, rsi_lookback : int = 48, rsi_min : float = 0,
                                     confirmation_mult: float=1.0, atr_min : float = 0.001):
    ohlcv = ohlcv.reset_index()  # Reset the index

    numeric_cols = ohlcv.select_dtypes(include=[np.number]).columns
    ohlcv[numeric_cols] = np.log(ohlcv[numeric_cols])

    close = ohlcv['close'].to_numpy()

    # Calculate ATR
    atr_arr = ta.atr(ohlcv['high'], ohlcv['low'],ohlcv['close'], atr_lookback)
    atr_arr = atr_arr.to_numpy()

    np.set_printoptions(threshold=np.inf)

    rsi_atr = ta.rsi(ohlcv['close'], rsi_lookback)
    rsi_atr = rsi_atr.to_numpy()

    trades = pd.DataFrame()
    trade_i = 0

    in_trade = False
    tp_price = None
    sl_price = None
    hp_i = None

    directional_change = DirectionalChange(sigma=sigma)

    # ohlcv_modified = ohlcv.copy()
    # ohlcv_modified['high'] = ohlcv_modified['close']
    # ohlcv_modified['low'] = ohlcv_modified['close']
    extremes_df = directional_change.get_extremes(ohlcv)
    all_extremes = extremes_df.extremes

    print(extremes_df.extremes)

    zone_bounds_plotting = {}
    extremes_in_zone_plotting = {}

    for i in range(lookback, len(ohlcv)):
        extremes = all_extremes.loc[(all_extremes['conf_time'] <= i) & (all_extremes.index >= i - lookback)].copy()

        current_zone = (close[i] - zone_size/2, close[i] + zone_size/2)

        extremes_in_zone = extremes[(extremes['extreme'].apply(lambda z: current_zone[0] <= z <= current_zone[1]))]

        count_extremes_in_zone = len(extremes_in_zone)

        if not in_trade and count_extremes_in_zone >= min_bounces and atr_arr[i] > atr_min:
            #1 is from top, 0 is from bottom
            entry_direction = None
            for j in range(i, i - lookback, -1):
                if close[j] > current_zone[1]:
                    entry_direction = 1
                    break
                elif close[j] < current_zone[0]:
                    entry_direction = 0
                    break

            in_trade = True

            if entry_direction==1:
                trades.loc[trade_i, 'confirmation'] = close[i] + confirmation_mult * atr_arr[i]
            elif entry_direction==0:
                trades.loc[trade_i, 'confirmation'] = close[i] - confirmation_mult * atr_arr[i]
            trades.loc[trade_i, 'confirmation_hp_i'] = i + confirmation_wait
            trades.loc[trade_i, 'type'] = entry_direction
            trades.loc[trade_i, 'potential'] = True

            zone_bounds_plotting[trade_i] = current_zone

            extremes_in_zone_plotting[trade_i] = (extremes_in_zone.index.tolist(), extremes_in_zone['extreme'].tolist())

        if in_trade and trades.loc[trade_i, 'potential'] == True:
            if (trades.loc[trade_i, 'type']==1 and (close[i] >= trades.loc[trade_i, 'confirmation'])) or \
                    (trades.loc[trade_i, 'type']==0 and (close[i] <= trades.loc[trade_i, 'confirmation'])):
                trades.loc[trade_i, 'potential'] = False
                trades.loc[trade_i, 'sl'] = close[i] - atr_arr[i] * sl_mult if trades.loc[trade_i, 'type']==1 else close[i] + atr_arr[i]*sl_mult
                trades.loc[trade_i, 'tp'] = close[i] + atr_arr[i] * tp_mult if trades.loc[trade_i, 'type']==1 else close[i] - atr_arr[i]*tp_mult
                trades.loc[trade_i, 'entry_i'] = i
                trades.loc[trade_i, 'entry_p'] = close[i]
                trades.loc[trade_i, 'hp_i'] = i + hold_period
            elif i >= trades.loc[trade_i, 'confirmation_hp_i']:
                in_trade = False
                trade_i += 1

        if in_trade and trades.loc[trade_i, 'potential'] == False:
            if (trades.loc[trade_i, 'type'] == 1 and (close[i] >= trades.loc[trade_i, 'tp'] or close[i] <= trades.loc[trade_i, 'sl'])) or \
                    (trades.loc[trade_i, 'type'] == 0 and (close[i] <= trades.loc[trade_i, 'tp'] or close[i] >= trades.loc[trade_i, 'sl'])) or \
                    (i >= trades.loc[trade_i, 'hp_i']):
                trades.loc[trade_i, 'exit_i'] = i
                trades.loc[trade_i, 'exit_p'] = close[i]

                if plot_graphs:
                    # Plotting the results
                    plt.figure(figsize=(14, 7))

                    print(trades.loc[trade_i, 'entry_p'], trades.loc[trade_i, 'exit_p'])

                    if (trades.loc[trade_i, 'exit_p'] - trades.loc[trade_i, 'entry_p'] > 0 and trades.loc[trade_i, 'type'] == 1) or \
                            (trades.loc[trade_i, 'entry_p'] - trades.loc[trade_i, 'exit_p'] > 0 and trades.loc[trade_i, 'type'] == 0):
                        plt.text(0.5, 1.075, "Success", fontsize=20, fontweight='bold', color='green',
                                 horizontalalignment='center', transform=plt.gca().transAxes)
                    else:
                        plt.text(0.5, 1.075,
                                 "Failure",
                                 fontsize=20, fontweight='bold', color='red', horizontalalignment='center',
                                 transform=plt.gca().transAxes)

                    # Plotting close prices
                    plt.plot(ohlcv['close'].iloc[int(trades.loc[trade_i, 'entry_i']) - lookback:i+1], label='Close Prices', color='blue', linewidth=2)

                    # Plotting the zone min and max as a filled area
                    plt.fill_between(range(int(trades.loc[trade_i, 'entry_i'])-lookback, i+1),
                                     zone_bounds_plotting[trade_i][0], zone_bounds_plotting[trade_i][1],
                                     color='green', alpha=0.3, label='Zone Area')

                    # Plotting take profit and stop loss levels
                    plt.axhline(y=trades.loc[trade_i, 'tp'], color='green', linestyle='--', label='Take Profit', linewidth=3)
                    plt.axhline(y=trades.loc[trade_i, 'sl'], color='red', linestyle='--', label='Stop Loss', linewidth=3)
                    plt.axvline(x=trades.loc[trade_i, 'entry_i'], color='black',linestyle=':', label='Entry Point', linewidth=2.5)

                    # Plotting extremes
                    plt.plot(all_extremes.loc[(all_extremes.index <= i+1) & (all_extremes.index >= int(trades.loc[trade_i, 'entry_i']) - lookback)].copy()['extreme'],
                                color='purple', label='Extremes', zorder=5, linewidth=2, alpha=0.5)

                    plt.scatter(extremes_in_zone_plotting[trade_i][0], extremes_in_zone_plotting[trade_i][1], color='red', s=30, zorder=6)

                    # Plotting high and low prices as a translucent background

                    plt.fill_between(range(int(trades.loc[trade_i, 'entry_i'])-lookback, i+1), ohlcv['high'].iloc[int(trades.loc[trade_i, 'entry_i']) - lookback:i+1],
                                     ohlcv['low'].iloc[int(trades.loc[trade_i, 'entry_i']) - lookback:i+1],
                                     color='gray', alpha=0.3, label='High-Low Range')

                    plt.title(f'Support and Resistance Strategy from {ohlcv["date"].iloc[int(trades.loc[trade_i, "entry_i"]) - lookback]} to {ohlcv["date"].iloc[i+1]}')
                    plt.xlabel('Time Index')
                    plt.ylabel('Price')
                    plt.legend()
                    plt.grid()
                    plt.show()

                in_trade = False
                trade_i += 1

    trades = trades.dropna()

    if len(trades) > 0:
        trades['return'] = trades.apply(
            lambda row: row['exit_p'] - row['entry_p'] if row['type'] == 1
            else row['entry_p'] - row['exit_p'],
            axis=1
        )

    print(trades['return'])

    return trades

if __name__ == "__main__":
    instruments = ["C:EURUSD", "C:EURJPY", "C:EURGBP", "C:GBPUSD", "C:AUDCAD"]
    # instruments = ["C:EURUSD", "C:EURJPY", "C:EURGBP", "C:AUDCAD", "C:AUDCHF"]

    instrument = "C:USDJPY"

    start = '2023-09-18'
    end = '2024-09-18'
    granularity = ['1', 'hour']

    # total_win_count = 0
    # total_trade_count = 0
    # all_profit = 0

    # for instrument in instruments:
    #     print("Fetching data...")
    #     api = PolygonAPI()
    #     df = api.get_data([instrument], start, end, granularity)[instrument]
    #
    #     print("Running strategy...")
    #     trades = support_and_resistance_rejection(df, plot_graphs=False, sigma=0.0025, min_bounces=2, zone_size = 0.002, confirmation_mult = 3.0)
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
    # win_rate = (total_win_count / total_trade_count) * 100 if total_trade_count > 0 else 0
    # #
    print("Fetching data...")
    api = PolygonAPI()
    df = api.get_data([instrument], start, end, granularity)[instrument]

    print("Running strategy...")
    trades = support_and_resistance_rejection(df, plot_graphs=False, sigma=0.0025, min_bounces=2, zone_size = 0.002, confirmation_mult=2.0, atr_min=0.001)

    # Calculate total profit
    total_profit = trades['return'].sum() if len(trades)>0 else 0

    # Calculate win rate
    win_count = (trades['return'] > 0).sum() if len(trades)>0 else 0
    total_trades = len(trades)
    win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0

    print(f"Total Profit {total_profit}")
    print(f"Win Rate: {win_rate}")
    print(f"Total Trades: {total_trades}")

    # Print the results
    # print(f'Total Profit: {all_profit}')
    # print(f'Win Rate: {win_rate:.2f}%')
    # print(f'Total Trade Count: {total_trade_count}')
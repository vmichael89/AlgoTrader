import os
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt
os.chdir("..")
from trader.algos.directional_change import DirectionalChange
from trader.broker import PolygonAPI
os.chdir("trader")

# Define the main function
def directional_trades(ohlcv: pd.DataFrame, lookback: int = 100, atr_lookback: int = 100, hold_period = 48,
                                     tp_mult : float=3.0, sl_mult : float=3.0, plot_graphs : bool = False, sigma : float = 0.0025,
                                     max_tolerance : int = 3, atr_min : float = 0.0010):
    ohlcv = ohlcv.reset_index()  # Reset the index

    numeric_cols = ohlcv.select_dtypes(include=[np.number]).columns
    ohlcv[numeric_cols] = np.log(ohlcv[numeric_cols])

    close = ohlcv['close'].to_numpy()

    # Calculate ATR
    atr_arr = ta.atr(ohlcv['high'], ohlcv['low'],ohlcv['close'], atr_lookback)
    atr_arr = atr_arr.to_numpy()

    trades = pd.DataFrame()
    trade_i = 0

    in_trade = False
    tp_price = None
    sl_price = None
    hp_i = None

    directional_change = DirectionalChange(sigma=sigma)
    all_extremes = directional_change.get_extremes(ohlcv).extremes
    all_extremes['conf_time'] = all_extremes['conf_time'].astype(int)

    for i in range(lookback, len(ohlcv)):
        potential_extreme = all_extremes.loc[
            (all_extremes.index >= i - max_tolerance) & (all_extremes['conf_time'] <= i), 'type']

        if len(potential_extreme)!=0:
            potential_extreme = potential_extreme.iloc[-1]

        if not in_trade and len(potential_extreme)!=0 and atr_arr[i]>=atr_min:
            in_trade = True

            trades.loc[trade_i, 'sl'] = close[i] - atr_arr[i] * sl_mult if potential_extreme=='bottom' else close[i] + atr_arr[i]*sl_mult
            trades.loc[trade_i, 'tp'] = close[i] + atr_arr[i] * sl_mult if potential_extreme=='bottom' else close[i] - atr_arr[i]*sl_mult
            trades.loc[trade_i, 'hp_i'] = i + hold_period
            trades.loc[trade_i, 'type'] = 1 if potential_extreme=="bottom" else 0
            trades.loc[trade_i, 'entry_p'] = close[i]
            trades.loc[trade_i, 'entry_i'] = i

        if in_trade:
            if (trades.loc[trade_i, 'type'] == 1 and (close[i] >= trades.loc[trade_i, 'tp'] or close[i] <= trades.loc[trade_i, 'sl'])) or \
                    (trades.loc[trade_i, 'type'] == 0 and (close[i] <= trades.loc[trade_i, 'tp'] or close[i] >= trades.loc[trade_i, 'sl'])) or \
                    (i >= trades.loc[trade_i, 'hp_i']):
                trades.loc[trade_i, 'exit_i'] = i
                trades.loc[trade_i, 'exit_p'] = close[i]

                in_trade = False
                trade_i += 1

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

    instrument = "C:USDJPY"

    start = '2014-09-18'
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
    trades = directional_trades(df, plot_graphs=False, sigma=0.0025, atr_min=0.002)

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
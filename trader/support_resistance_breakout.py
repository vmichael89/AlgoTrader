from algos.directional_change import DirectionalChange
from broker import PolygonAPI
import pandas as pd
import numpy as np
import pandas_ta as ta

# Define the assign_to_zone function
def assign_to_zone(price, zones):
    for i in range(len(zones) - 1):
        if zones[i] <= price <= zones[i + 1]:
            return (zones[i], zones[i + 1])

    return (None, None)

# Define the main function
def support_and_resistance_rejection(ohlcv: pd.DataFrame, lookback: int = 240, atr_lookback: int = 168, hold_period = 48,
                                     tp_mult : float=3.0, sl_mult : float=3.0):
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

    for i in range(lookback, len(ohlcv)):
        directional_change = DirectionalChange(sigma=0.0025)
        extremes = directional_change.get_extremes(ohlcv.iloc[i - lookback : i]).extremes

        extreme_prices = extremes['extreme'].values

        price_min = extreme_prices.min()
        price_max = extreme_prices.max()
        zone_size = 0.002

        zones = np.arange(price_min, price_max + zone_size, zone_size)

        extremes['assigned_zone'] = extremes['extreme'].apply(lambda x: assign_to_zone(x, zones))

        extremes_in_zone = extremes[(extremes['assigned_zone'].apply(lambda z: z[0] <= close[i] < z[1]))]
        count_extremes_in_zone = len(extremes_in_zone)

        if not in_trade and count_extremes_in_zone >= 2:
            current_zone = assign_to_zone(close[i], zones)

            #1 is from top, 0 is from bottom
            entry_direction = None
            for j in range(i, i - lookback, -1):
                if close[j] > current_zone[1]:
                    entry_direction = 1
                elif close[j] < current_zone[0]:
                    entry_direction = 0

            if entry_direction == 1:
                tp_price = close[i] + atr_arr[i] * tp_mult
                sl_price = close[i] - atr_arr[i] * sl_mult
            elif entry_direction == 0:
                tp_price = close[i] - atr_arr[i] * tp_mult
                sl_price = close[i] + atr_arr[i] * sl_mult

            hp_i = i + hold_period
            in_trade = True

            trades.loc[trade_i, 'entry_i'] = i
            trades.loc[trade_i, 'entry_p'] = close[i]
            trades.loc[trade_i, 'atr'] = atr_arr[i]
            trades.loc[trade_i, 'sl'] = sl_price
            trades.loc[trade_i, 'tp'] = tp_price
            trades.loc[trade_i, 'hp_i'] = i + hold_period
            trades.loc[trade_i, 'type'] = entry_direction

        if in_trade:
            if (trades.loc[trade_i, 'type'] == 1 and (close[i] >= tp_price or close[i] <= sl_price)) or \
                    (trades.loc[trade_i, 'type'] == 0 and (close[i] <= tp_price or close[i] >= sl_price)) or \
                    (i >= hp_i):
                trades.loc[trade_i, 'exit_i'] = i
                trades.loc[trade_i, 'exit_p'] = close[i]

                in_trade = False
                trade_i += 1

    trades['return'] = trades.apply(
        lambda row: row['exit_p'] - row['entry_p'] if row['type'] == 1
        else row['entry_p'] - row['exit_p'],
        axis=1
    )

    return trades

if __name__ == "__main__":
    instrument = "C:USDJPY"

    start = '2014-09-18'
    end = '2024-09-18'
    granularity = ['1', 'hour']

    api = PolygonAPI()
    df = api.get_data([instrument], start, end, granularity)[instrument]
    trades = support_and_resistance_rejection(df)

    # Calculate total profit
    total_profit = trades['return'].sum()

    # Calculate win rate
    win_count = (trades['return'] > 0).sum()
    total_trades = len(trades)
    win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0

    # Print the results
    print(f'Total Profit: {total_profit}')
    print(f'Win Rate: {win_rate:.2f}%')
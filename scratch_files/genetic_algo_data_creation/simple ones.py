import pandas as pd
import os
import pandas_ta as ta
import matplotlib.pyplot as plt
from trader.algos.directional_change import DirectionalChange
import numpy as np
from trader.algos.trendline_automation import fit_trendlines_single
import mplfinance as mpl

data_path = '../../data/all_data'
data_features_path = '../../data/data_features'
files = os.listdir(data_path)

def save_new_features(data_path, data_features_path, file):
    ohlcv = pd.read_csv(os.path.join(data_path, file))
    new_dataframe = chain_functions(ohlcv)
    new_dataframe.to_csv(os.path.join(data_features_path, file))

def chain_functions(ohlcv):
    ohlcv = find_features(ohlcv)
    ohlcv = highs_and_lows(ohlcv)
    ohlcv = trendline_breakout(ohlcv)
    ohlcv = moving_average_crossover(ohlcv)
    ohlcv = bollinger_band_cross(ohlcv)
    ohlcv = pullbacks(ohlcv)
    ohlcv = def_levels(ohlcv)

    return ohlcv

def find_features(ohlcv):
    rsi = ta.rsi(ohlcv['close'], 14)

    ohlcv['RSI3070'] = 0  # Default to 0
    ohlcv.loc[rsi < 30, 'RSI3070'] = 1
    ohlcv.loc[rsi > 70, 'RSI3070'] = -1

    ohlcv['RSI4060'] = 0  # Default to 0
    ohlcv.loc[rsi < 40, 'RSI4060'] = 1
    ohlcv.loc[rsi > 60, 'RSI4060'] = -1

    ma15 = ohlcv['close'].rolling(15).mean()
    ma50 = ohlcv['close'].rolling(50).mean()
    ma100 = ohlcv['close'].rolling(100).mean()

    ohlcv['PAB15MA'] = 0  # Default to 0
    ohlcv.loc[ohlcv['close']>ma15, 'PAB15MA'] = 1
    ohlcv.loc[ohlcv['close']<ma15, 'PAB15MA'] = -1

    ohlcv['PAB50MA'] = 0  # Default to 0
    ohlcv.loc[ohlcv['close'] > ma50, 'PAB50MA'] = 1
    ohlcv.loc[ohlcv['close'] < ma50, 'PAB50MA'] = -1

    ohlcv['PAB100MA'] = 0  # Default to 0
    ohlcv.loc[ohlcv['close'] > ma100, 'PAB100MA'] = 1
    ohlcv.loc[ohlcv['close'] < ma100, 'PAB100MA'] = -1

    atr150 = ta.atr(ohlcv['high'], ohlcv['low'],ohlcv['close'], 150)
    atr2500 = ta.atr(ohlcv['high'], ohlcv['low'],ohlcv['close'], 2500)
    atr_ratio = atr150/atr2500

    ohlcv['ATRTA'] = 0
    ohlcv.loc[atr_ratio > 1.1, 'ATRTA'] = 2

    ohlcv['ATRTB'] = 0
    ohlcv.loc[atr_ratio < 1.1, 'ATRTB'] = 2

    # Initialize columns for indecision and hammer patterns
    ohlcv['INDEC'] = 0  # Default value
    ohlcv['HAMMER'] = 0

    # Iterate through each row to apply the conditions
    for index, row in ohlcv.iterrows():
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        low_price = row['low']

        # Calculate values directly without creating DataFrame columns
        body_size = abs(open_price - close_price)
        high_low_range = high_price - low_price
        lower_wick = min(open_price, close_price) - low_price
        upper_wick = high_price - max(open_price, close_price)

        # Check for indecision candle
        if body_size < (high_low_range / 10) and (upper_wick <= 3 * lower_wick and lower_wick <= 3 * upper_wick):
            ohlcv.at[index, 'INDEC'] = 2  # Indecision candle

        # Check for hammer and inverted hammer
        elif upper_wick <= (1 / 3) * lower_wick:
            ohlcv.at[index, 'HAMMER'] = 1  # Hammer
        elif lower_wick <= (1 / 3) * upper_wick:
            ohlcv.at[index, 'HAMMER'] = -1  # Inverted hammer

    ohlcv['ENGULF'] = 0  # Default value

    # Iterate through each row starting from the second candle
    for index in range(1, len(ohlcv)):
        prev_open = ohlcv.at[index - 1, 'open']
        prev_close = ohlcv.at[index - 1, 'close']
        curr_open = ohlcv.at[index, 'open']
        curr_close = ohlcv.at[index, 'close']

        # Check for green engulfing pattern
        if (curr_close > prev_open and curr_open < prev_close) and (curr_close > curr_open and prev_close < prev_open):
            ohlcv.at[index, 'ENGULF'] = 1  # Engulfing green candle

        # Check for red engulfing pattern
        elif (curr_open > prev_close and curr_close < prev_open) and (
                curr_close < curr_open and prev_close > prev_open):
            ohlcv.at[index, 'ENGULF'] = -1  # Engulfing red candle

    body_size_ratio = (ohlcv['close'] - ohlcv['open'])/atr150

    ohlcv['BIGCAND'] = 0
    ohlcv.loc[body_size_ratio > 0.5, 'BIGCAND'] = 1
    ohlcv.loc[body_size_ratio < -0.5, 'BIGCAND'] = -1

    adx = ta.adx(ohlcv['high'], ohlcv['low'],ohlcv['close'])['ADX_14']

    ohlcv['ADXTA'] = 0
    ohlcv.loc[adx > 25, 'ADXTA'] = 2

    ohlcv['ADXTB'] = 0
    ohlcv.loc[adx < 25, 'ADXTB'] = 2

    mean_vol = ohlcv['volume'].rolling(250).mean()
    ohlcv['RELVOL'] = 0
    ohlcv.loc[(ohlcv['volume']/mean_vol) > 1.4, 'RELVOL'] = 2

    return ohlcv

def highs_and_lows(ohlcv):
    ohlcv_log = ohlcv.copy()
    numeric_cols = ohlcv_log.select_dtypes(include=[np.number]).columns
    ohlcv_log[numeric_cols] = np.log(ohlcv_log[numeric_cols])

    directional_change = DirectionalChange(sigma=0.00042)
    all_extremes = directional_change.get_extremes(ohlcv_log).extremes
    all_extremes['conf_time'] = all_extremes['conf_time'].astype(int)

    extreme_tops = all_extremes[all_extremes['type'] == 'top']
    extreme_bottoms = all_extremes[all_extremes['type'] == 'bottom']

    # Initialize columns for higher highs and lower lows
    ohlcv['HH0'] = 0
    ohlcv['HH1'] = 0
    ohlcv['HL0'] = 0
    ohlcv['HL1'] = 0
    ohlcv['LH0'] = 0
    ohlcv['LH1'] = 0
    ohlcv['LL0'] = 0
    ohlcv['LL1'] = 0

    # Iterate through each candle in the ohlcv DataFrame
    for idx in range(len(ohlcv)):
        # Slice extreme_tops and extreme_bottoms
        current_tops = extreme_tops[extreme_tops['conf_time'] < ohlcv.index[idx]]
        current_bottoms = extreme_bottoms[extreme_bottoms['conf_time'] < ohlcv.index[idx]]

        # Check conditions for higher highs and lower lows
        if len(current_tops) >= 2:
            if current_tops.iloc[-1]['extreme'] > current_tops.iloc[-2]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'HH0'] = 2
            if current_tops.iloc[-1]['extreme'] < current_tops.iloc[-2]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'LH0'] = 2
            if len(current_tops) >= 3 and current_tops.iloc[-2]['extreme'] > current_tops.iloc[-3]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'HH1'] = 2
            if len(current_tops) >= 3 and current_tops.iloc[-2]['extreme'] < current_tops.iloc[-3]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'LH1'] = 2

        if len(current_bottoms) >= 2:
            if current_bottoms.iloc[-1]['extreme'] < current_bottoms.iloc[-2]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'LL0'] = 2
            if current_bottoms.iloc[-1]['extreme'] > current_bottoms.iloc[-2]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'HL0'] = 2
            if len(current_bottoms) >= 3 and current_bottoms.iloc[-2]['extreme'] < current_bottoms.iloc[-3]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'LL1'] = 2
            if len(current_bottoms) >= 3 and current_bottoms.iloc[-2]['extreme'] > current_bottoms.iloc[-3]['extreme']:
                ohlcv.at[ohlcv.index[idx], 'HL1'] = 2

    return ohlcv

def trendline_breakout(ohlcv):
    ohlcv = ohlcv.copy()

    close = np.log(ohlcv['close'].to_numpy())

    ohlcv['TRNDLN72'] = 0
    ohlcv['TRNDLN144'] = 0

    for i in range(72, len(ohlcv)):
        window = close[i - 72: i]
        s_coefs, r_coefs = fit_trendlines_single(window)
        r_val = r_coefs[1] + 72 * r_coefs[0]
        s_val = s_coefs[1] + 72 * s_coefs[0]

        if close[i] > r_val:
            ohlcv.loc[i, 'TRNDLN72'] = 1
        elif close[i] < s_val:
            ohlcv.loc[i, 'TRNDLN72'] = -1

        if i>=144:
            window = close[i - 144: i]
            s_coefs, r_coefs = fit_trendlines_single(window)
            r_val = r_coefs[1] + 144 * r_coefs[0]
            s_val = s_coefs[1] + 144 * s_coefs[0]

            if close[i] > r_val:
                ohlcv.loc[i, 'TRNDLN144'] = 1
            elif close[i] < s_val:
                ohlcv.loc[i, 'TRNDLN144'] = -1

    return ohlcv

def moving_average_crossover(ohlcv):
    # Calculate moving averages
    ma15 = ohlcv['close'].rolling(15).mean()
    ma50 = ohlcv['close'].rolling(50).mean()
    ma100 = ohlcv['close'].rolling(100).mean()

    # Create crossover columns
    ohlcv['MACRS1550'] = 0
    ohlcv['MACRS50100'] = 0

    # Identify cross points for MA15 and MA50
    for i in range(1, len(ohlcv)):
        if ma15[i] > ma50[i] and ma15[i - 1] <= ma50[i - 1]:
            ohlcv.at[ohlcv.index[i], 'MACRS1550'] = 1  # 15 crosses above 50
        elif ma15[i] < ma50[i] and ma15[i - 1] >= ma50[i - 1]:
            ohlcv.at[ohlcv.index[i], 'MACRS1550'] = -1  # 15 crosses below 50

    # Identify cross points for MA50 and MA100
    for i in range(1, len(ohlcv)):
        if ma50[i] > ma100[i] and ma50[i - 1] <= ma100[i - 1]:
            ohlcv.at[ohlcv.index[i], 'MACRS50100'] = 1  # 50 crosses above 100
        elif ma50[i] < ma100[i] and ma50[i - 1] >= ma100[i - 1]:
            ohlcv.at[ohlcv.index[i], 'MACRS50100'] = -1  # 50 crosses below 100

    return ohlcv

def bollinger_band_cross(ohlcv):
    # Calculate the 20-day moving average and standard deviation
    ma20 = ohlcv['close'].rolling(20).mean()
    std20 = ohlcv['close'].rolling(20).std()

    # Calculate the upper and lower Bollinger Bands
    upper_band = ma20 + (2 * std20)
    lower_band = ma20 - (2 * std20)

    # Create the BLBND column initialized to 0
    ohlcv['BLBND'] = 0

    # Identify cross points for Bollinger Bands
    for i in range(1, len(ohlcv)):
        if ohlcv['close'][i] > upper_band[i] and ohlcv['close'][i - 1] <= upper_band[i - 1]:
            ohlcv.at[ohlcv.index[i], 'BLBND'] = -1  # Crosses upper band from below
        elif ohlcv['close'][i] < lower_band[i] and ohlcv['close'][i - 1] >= lower_band[i - 1]:
            ohlcv.at[ohlcv.index[i], 'BLBND'] = 1  # Crosses lower band from above

    return ohlcv

def pullbacks(ohlcv):
    ohlcv_log = ohlcv.copy()
    numeric_cols = ohlcv_log.select_dtypes(include=[np.number]).columns
    ohlcv_log[numeric_cols] = np.log(ohlcv_log[numeric_cols])

    directional_change = DirectionalChange(sigma=0.00042)
    all_extremes = directional_change.get_extremes(ohlcv_log).extremes
    all_extremes['conf_time'] = all_extremes['conf_time'].astype(int)

    close = np.log(ohlcv['close'].to_numpy())

    ohlcv['PLBCK'] = 0

    for i in range(250, len(ohlcv)):
        extremes = all_extremes.loc[all_extremes['conf_time'] <= i].copy()

        if extremes.iloc[-1]['type']=='top' and extremes.iloc[-2]['type']=='bottom' and \
                extremes.iloc[-2]['extreme'] <= close[i] <= (1 - 0.5) * extremes.iloc[-2]['extreme'] + 0.5 * extremes.iloc[-1]['extreme']:
            ohlcv.loc[i, 'PLBCK'] = 1

        if extremes.iloc[-1]['type']=='bottom' and extremes.iloc[-2]['type']=='top' and \
                extremes.iloc[-2]['extreme'] >= close[i] >= (1 - 0.5) * extremes.iloc[-2]['extreme'] + 0.5 * extremes.iloc[-1]['extreme']:
            ohlcv.loc[i, 'PLBCK'] = -1

    print(ohlcv)
    return(ohlcv)

def def_levels(ohlcv):
    atr150 = ta.atr(ohlcv['high'], ohlcv['low'], ohlcv['close'], 150)

    ohlcv['A2'] = ohlcv['close'] + atr150*2
    ohlcv['A3'] = ohlcv['close'] + atr150 * 3
    ohlcv['A4'] = ohlcv['close'] + atr150 * 4

    ohlcv['B2'] = ohlcv['close'] - atr150 * 2
    ohlcv['B3'] = ohlcv['close'] - atr150 * 3
    ohlcv['B4'] = ohlcv['close'] - atr150 * 4

    print(ohlcv[:3000])
    return ohlcv
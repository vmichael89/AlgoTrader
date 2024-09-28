import os
os.chdir("..")
from trader.algos.directional_change import DirectionalChange
from trader.broker import PolygonAPI
os.chdir("trader")
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
def support_and_resistance_rejection(df: pd.DataFrame, min_touches_sr=2, lookback: int = 240, atr_lookback: int = 168, hold_period=48,
                                     tp_mult: float = 3.0, sl_mult: float = 3.0):
    # ohlcv = ohlcv.reset_index()  # Reset the index
    df = df.copy()

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = np.log(df[numeric_cols])

    # Calculate ATR
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], atr_lookback)

    trades = pd.DataFrame()
    trade_i = 0

    in_trade = False
    tp_price = None
    sl_price = None
    hp_i = None

    for window in df.rolling(window=lookback):
        window = window.copy()  # will otherwise trigger a pandas warning not to operate on a view

        current_timestamp = window.index[-1]
        i = df.index.get_loc(window.index[-1])

        if i < lookback:
            continue  # wait until window has it's full length, i.e. len(window)=lookback

        current_close = window.iloc[-1].close
        current_atr = window.iloc[-1].atr

        price_min = window['extreme'].min()
        price_max = window['extreme'].max()
        zone_size = 0.002

        zones = np.arange(price_min, price_max + zone_size, zone_size)
        current_zone = assign_to_zone(current_close, zones)

        window['assigned_zone'] = window['extreme'].apply(lambda x: assign_to_zone(x, zones))
        # tuples of (zone_begin, zone_end) or (None, None) if not in any zone

        count_extremes_in_zone = window['assigned_zone'].value_counts().get(current_zone, 0)
        # returns 0 if zone tuple was not found

        if not in_trade and count_extremes_in_zone >= min_touches_sr:

            # 1 is from top, 0 is from bottom
            entry_direction = None
            # Iterate BACKWARDS over rows within the window
            for _, row in window.iloc[::-1].iterrows():
                if current_zone == (None, None):
                    continue  # would otherwise throw an error at row['close'] > None
                if row['close'] > current_zone[1]:
                    entry_direction = 1
                    break  # exits when direction is evaluated
                elif row['close'] < current_zone[0]:
                    entry_direction = 0
                    break  # exits when direction is evaluated

            if entry_direction == 1:
                tp_price = current_close + current_atr * tp_mult
                sl_price = current_close - current_atr * sl_mult
            elif entry_direction == 0:
                tp_price = current_close - current_atr * tp_mult
                sl_price = current_close + current_atr * sl_mult

            hp_i = i + hold_period
            in_trade = True

            trades.loc[trade_i, 'entry_i'] = i
            trades.loc[trade_i, 'entry_time'] = current_timestamp
            trades.loc[trade_i, 'entry_p'] = current_close
            trades.loc[trade_i, 'atr'] = current_atr
            trades.loc[trade_i, 'sl'] = sl_price
            trades.loc[trade_i, 'tp'] = tp_price
            trades.loc[trade_i, 'hp_i'] = i + hold_period
            trades.loc[trade_i, 'type'] = entry_direction

        if in_trade:
            if (trades.loc[trade_i, 'type'] == 1 and (current_close >= tp_price or current_close <= sl_price)) or \
                    (trades.loc[trade_i, 'type'] == 0 and (current_close <= tp_price or current_close >= sl_price)) or \
                    (i >= hp_i):
                trades.loc[trade_i, 'exit_i'] = i
                trades.loc[trade_i, 'exit_time'] = current_timestamp
                trades.loc[trade_i, 'exit_p'] = current_close

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
    start = '2019-09-01'
    end = '2019-12-01'
    granularity = ['1', 'hour']

    sigma = 0.0025

    filestr = f"{instrument[2:]}-{start}-{end}-{''.join(granularity)}.pkl"
    filestr_wsig = f"{instrument[2:]}-{start}-{end}-{''.join(granularity)}-sig{sigma}.pkl"


    print("Getting data")
    try:
        print("  from file")
        df = pd.read_pickle(filestr)
    except:
        print("  from api")
        api = PolygonAPI()
        df = api.get_data([instrument], start, end, granularity)[instrument]
        df.to_pickle(filestr)

    print("Getting directional change")
    try:
        print("  from file")
        df = pd.read_pickle(filestr_wsig)
    except:
        print("  calculated")
        dc = DirectionalChange(sigma=sigma).get_extremes(df)
        df['extreme'] = dc.extremes['extreme']
        df['extreme_type'] = dc.extremes['type']
        df.to_pickle(filestr_wsig)

    # df = df[:1000]  # for quick testing
    print("Running strategy")
    for min_touches in range(2, 3, 2):
        trades = support_and_resistance_rejection(df, min_touches)
        trades = trades.dropna(subset='exit_time')
        # Calculate total profit
        total_profit = trades['return'].sum()

        # Calculate win rate
        win_count = (trades['return'] > 0).sum()
        total_trades = len(trades)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0

        # Print the results
        print(f'Min touches: {min_touches:2} - Win Rate: {win_rate:.2f}% - Total Profit: {total_profit}')

        import dash
        from dash import dcc, html
        from dash.dependencies import Input, Output
        import plotly.graph_objects as go

        app = dash.Dash(__name__)

        def create_initial_figure():
            # plot all data
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df.open, high=df.high, low=df.low, close=df.close)])
            fig.update_layout(title=str("data"), xaxis_rangeslider_visible=False)  # hide slider

            # plot directional change
            fig.add_scatter(x=df['extreme'].dropna().index, y=df['extreme'].dropna(), line_color='black')

            for trade_type in (0, 1):
                color = ('red', 'green')[trade_type]
                marker_in = ('triangle-up', 'triangle-down')[trade_type]
                marker_out = ('triangle-down', 'triangle-up')[trade_type]
                # Plot entry markers
                fig.add_trace(go.Scatter(
                    x=trades.loc[trades['type'] == trade_type, 'entry_time'],
                    y=df.loc[trades.loc[trades['type'] == trade_type, 'entry_time'], 'close'],
                    mode='markers',
                    marker=dict(size=12, color=color, symbol=marker_in),
                ))

                # Plot exit markers
                fig.add_trace(go.Scatter(
                    x=trades.loc[trades['type'] == trade_type, 'exit_time'],
                    y=df.loc[trades.loc[trades['type'] == trade_type, 'exit_time'], 'close'],
                    mode='markers',
                    marker=dict(size=12, color=color, symbol=marker_out),
                ))

            return fig

        # Layout of the app
        app.layout = html.Div([
            dcc.Graph(id='candlestick-chart', figure=create_initial_figure()),  # Main chart
        ])

        app.run_server(debug=True)

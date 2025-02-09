import pandas as pd

SESSION_START_TIME = '08:00'
SESSION_END_TIME = '17:00'

ASIA_TIME_ZONE = 'Asia/Singapore'
AUSTRALIA_TIME_ZONE = 'Australia/Sydney'
ASIA_PACIFIC_TIME_ZONE = ('Asia/Singapore', 'Australia/Sydney')
US_TIME_ZONE = 'America/New_York'
EU_TIME_ZONE = 'Europe/London'

TZ_TO_ALIAS = {
    ASIA_PACIFIC_TIME_ZONE: 'Asia/Pacific',
    EU_TIME_ZONE: 'EU',
    US_TIME_ZONE: 'US'
}

ALIAS_TO_COLOR = {
    TZ_TO_ALIAS[ASIA_PACIFIC_TIME_ZONE]: 'darkgoldenrod',
    TZ_TO_ALIAS[EU_TIME_ZONE]: 'darkgreen',
    TZ_TO_ALIAS[US_TIME_ZONE]: 'darkred'
}


def is_ohlc_data(df):
    return {'open', 'high', 'low', 'close'}.issubset(df.columns)

def is_tick_data(df):
    return {'bid', 'ask'}.issubset(df.columns)

def get_data_column_names(df, price):
    # check input, price must be bid or ask
    assert price in {'bid', 'ask'}

    if is_ohlc_data(df):
        return 'open', 'high', 'low', 'close'
    elif is_tick_data(df):
        return price, price, price, price
    else:
        raise Exception('Data must have OHLC or tick columns')

def get_sessions(df: pd.DataFrame, price='bid'):
    # get df time zone
    tz = df.index.tz
    if tz is None:
        df = df.tz_localize('UTC')
    open, high, low, close = get_data_column_names(df, price=price)

    # Get all sessions
    all_sessions = []
    for combined_zones in [ASIA_PACIFIC_TIME_ZONE, EU_TIME_ZONE, US_TIME_ZONE]:
        combined_zones_tuple = (combined_zones,) if isinstance(combined_zones, str) else combined_zones
        sessions = []
        for time_zone in combined_zones_tuple:
            df_session = df.tz_convert(time_zone).between_time(SESSION_START_TIME, SESSION_END_TIME).resample('D').agg(
                open=(open, 'first'),
                high=(high, 'max'),
                low=(low, 'min'),
                close=(close, 'last'),
                session=(open, lambda x: TZ_TO_ALIAS[combined_zones]),  # 'open' any column will do
                # complete=(open, lambda x: x.index[-1].hour >= 16)  # 'open' any column will do
                start_time=(open, lambda x: x.index[0].tz_convert(tz) if not x.empty else None),
                end_time=(open, lambda x: x.index[-1].tz_convert(tz) if not x.empty else None)
            ).tz_localize(None).dropna()
            sessions.append(df_session)

        # Combine asia and australia sessions
        combined_sessions = pd.concat(sessions).sort_index()
        combined_sessions = combined_sessions.groupby(combined_sessions.index).agg(
            open=('open', 'first'),
            high=('high', 'max'),
            low=('low', 'min'),
            close=('close', 'last'),
            session=('session', 'first'),
            # complete=('complete', 'all')
            start_time=('start_time', 'min'),
            end_time=('end_time', 'max')
        )

        all_sessions.append(combined_sessions)

    # Concatenate all sessions
    sessions = pd.concat(all_sessions).sort_index()

    return sessions

def plot_sessions(df_sessions, fig=None):
    """Plot as rectangles from low to high"""
    import plotly.graph_objects as go

    if fig is None:
        fig = go.Figure()
    for idx, row in df_sessions.iterrows():
        fig.add_shape(
            type='rect',
            x0=row['start_time'],
            x1=row['end_time'],
            y0=row['low'],
            y1=row['high'],
            line=dict(color='white', width=1),
            fillcolor=ALIAS_TO_COLOR[row['session']],
            opacity=0.3,
            layer='below',
            label=dict(text=row['session'], textposition='top right')
        )
    return fig
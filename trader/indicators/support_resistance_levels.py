from datetime import timedelta
import plotly.graph_objects as go

from . import Indicator
from . import trading_session

SECOND = timedelta(seconds=1)
MINUTE = timedelta(minutes=1)
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
WEEK = timedelta(weeks=1)
MONTH = timedelta(days=30)
YEAR = timedelta(days=365)


class SupportResistance(Indicator):
    def __init__(self, data, high_colname='high', low_colname='low', granularity='1H'):
        """
        Initialize with historical data and granularity.

        Args:
        - data (pd.DataFrame): Historical price data with datetime index.
        - granularity (str): Granularity for time-based levels (e.g., '1H', '1D').
        """
        self.data = data
        self.high_colname = high_colname
        self.low_colname = low_colname
        self.granularity = granularity
        self.levels = []

    def plot_obj(self):
        """Return plotly graph objects."""
        return [go.Scatter(
            x=[level['datetime'], self.data.df.index[-1]],
            y=[level['price'], level['price']],
            mode='lines',
            line=dict(color='black', width=1),
            name=level['name']
        )
        for level in self.levels]


    def time_based_levels(self):
        """Calculate time-based support/resistance levels."""
        periods = [
            # 5 * MINUTE,
            # 15 * MINUTE,
            # 30 * MINUTE,
            # HOUR,
            # 3 * HOUR,
            # 6 * HOUR,
            # DAY,
            # WEEK
        ]

        # get highs and lows for each last period
        for period in periods:
            # get last period
            last_period = self.data.df.last(period)
            high = last_period[self.high_colname].max()
            idx_high = last_period[self.high_colname].idxmax()
            self.levels.append({'datetime': idx_high, 'price': high, 'name': f'{period} High'})
            low = last_period[self.low_colname].min()
            idx_low = last_period[self.low_colname].idxmin()
            self.levels.append({'datetime': idx_low, 'price': low, 'name': f'{period} Low'})

        # Previous session
        sessions = trading_session.get_sessions(self.data.df, price='bid')
        # last_session = sessions[sessions.complete].iloc[-1]
        last_session = sessions.iloc[-1]
        high = last_session['high']
        idx_high = last_session.name
        self.levels.append({'datetime': idx_high, 'price': high, 'name': 'Last session High'})
        low = last_session['low']
        idx_low = last_session.name
        self.levels.append({'datetime': idx_low, 'price': low, 'name': 'Last session Low'})

        # Previous day
        current_time = self.data.df.index[-1]
        # previous_day id floored to 00:00
        previous_day = current_time.floor('D') - DAY
        # data for previous day for 1 day duration
        previous_day_data = self.data.df.loc[previous_day:previous_day + DAY]
        high = previous_day_data[self.high_colname].max()
        idx_high = previous_day_data[self.high_colname].idxmax()
        self.levels.append({'datetime': idx_high, 'price': high, 'name': 'Last session High'})
        low = previous_day_data[self.low_colname].min()
        idx_low = previous_day_data[self.low_colname].idxmin()
        self.levels.append({'datetime': idx_low, 'price': low, 'name': 'Last session Low'})


    # def kernel_density_levels(self, bandwidth=0.01):
    #     """
    #     Calculate levels based on kernel density estimate.
    #
    #     Args:
    #     - bandwidth (float): Bandwidth for KDE.
    #     """
    #     pass  # Implementation
    #
    # def psychological_levels(self, step=0.05):
    #     """
    #     Calculate psychological levels based on round numbers.
    #
    #     Args:
    #     - step (float): Interval between psychological levels.
    #     """
    #     pass  # Implementation
    #
    # def pivot_points(self):
    #     """
    #     Calculate pivot points and support/resistance levels.
    #     """
    #     pass  # Implementation
    #
    # def moving_average_levels(self, periods=[50, 100, 200]):
    #     """
    #     Calculate levels based on moving averages.
    #
    #     Args:
    #     - periods (list): List of moving average periods.
    #     """
    #     pass  # Implementation


    def process_data_point(self, index, row):
        pass
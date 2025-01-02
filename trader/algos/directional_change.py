import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class DirectionalChange:
    EXTREME_COL_NAME = 'extreme'
    OVERSHOOT_COL_NAME = 'overshoot'

    def __init__(self, instrument, sigma=0.001, high_colname='high', low_colname='low'):
        self.instrument = instrument
        self.sigma = sigma
        self.high_colname = high_colname
        self.low_colname = low_colname
        self.overshoots = pd.DataFrame(
            columns=['overshoot', 'type'],
            index=pd.DatetimeIndex([],
            name='datetime'))
        self.extremes = pd.DataFrame(
            columns=['extreme', 'conf_time', 'type', 'total_price_movement', 'time_for_completion', 'retracement'],
            index=pd.DatetimeIndex([],
            name='datetime'))

        self.up_zig = False
        self.down_zig = False
        self.last_overshoot = 0 
        self.initial_timestamp = None
        self.initial_high = None
        self.initial_low = None
        self.timestamp = None

    def save_overshoot(self, time=None, val=None):
        """Saves `last_overshoot` at `timestamp` from outer scope if not specified"""
        if not time:
            time = self.timestamp
        if not val:
            val = self.last_overshoot
        self.overshoots.loc[time, self.OVERSHOOT_COL_NAME] = val

    def save_extreme(self):
        # get value and index from last saved overshoot event
        extreme_index = self.overshoots[self.OVERSHOOT_COL_NAME].index[-1]
        extreme_value = self.overshoots[self.OVERSHOOT_COL_NAME].iloc[-1]

        if self.extremes.empty:
            total_price_movement = 0
            time_for_completion = pd.Timedelta(0)
            retracement = 0
        else:
            prev_index = self.extremes.index[-1]
            prev_extreme = self.extremes.iloc[-1]['extreme']
            prev_total_price_movement = self.extremes.iloc[-1]['total_price_movement']
            total_price_movement = abs(extreme_value - prev_extreme)
            time_for_completion = extreme_index - prev_index
            retracement = 0 if prev_total_price_movement == 0 else total_price_movement / prev_total_price_movement

        # save
        self.extremes.loc[extreme_index] = {
            'extreme': extreme_value,
            'conf_time': self.timestamp,
            'type': 'top' if self.down_zig else 'bottom',
            'total_price_movement': total_price_movement,
            'time_for_completion': time_for_completion,
            'retracement': retracement
        }

    def get_extremes(self, df):
        # loop through df, omit everything except high and low
        for timestamp, row in df.iterrows():
            self.process_data_point(timestamp, row[self.high_colname], row[self.low_colname])

    def process_data_point(self, timestamp, high, low):
        self.timestamp = timestamp

        if not self.initial_timestamp:
            self.initial_timestamp = timestamp
            self.initial_high = high
            self.initial_low = low

        # trend initialization / wait for first overshoot event
        if not (self.up_zig or self.down_zig):
            if low <= self.initial_high - self.sigma:
                self.down_zig = True
                # save first high as first overshoot and first extreme
                self.save_overshoot(self.initial_timestamp, self.initial_high)
                self.save_extreme()
                # save time/val from current overshoot event
                self.last_overshoot = low
                self.save_overshoot()
            elif high >= self.initial_low + self.sigma:
                self.up_zig = True
                # save first low as first overshoot and first extreme
                self.save_overshoot(self.initial_timestamp, self.initial_low)
                self.save_extreme()
                # save time/val from current overshoot event
                self.last_overshoot = high
                self.save_overshoot()

        elif self.up_zig:
            if overshoot_event := high > self.last_overshoot:
                self.last_overshoot = high
                self.save_overshoot()
            elif low <= self.last_overshoot - self.sigma:
                self.down_zig = True
                self.up_zig = False
                self.save_extreme()
                self.last_overshoot = low
                self.save_overshoot()

        elif self.down_zig:
            if undershoot_event := low < self.last_overshoot:
                self.last_overshoot = low
                self.save_overshoot()
            elif high >= self.last_overshoot + self.sigma:
                self.up_zig = True
                self.down_zig = False
                self.save_extreme()
                self.last_overshoot = high
                self.save_overshoot()


class DirectionalChange2:
    def __init__(self, sigma):
        self.sigma = sigma
        self.line = None  # used to check if extremes have already been plotted
        self._reset_extremes()

    def _reset_extremes(self):
        self.up_zig = False
        self.tmp_max = None
        self.tmp_min = None
        self.tmp_max_i = -1
        self.tmp_min_i = -1
        self.extremes = pd.DataFrame(columns=['extreme', 'conf_time', 'type'],
                                     index=pd.DatetimeIndex([], name='time'))

    def process_data_point(self, index, high, low):
        if self.tmp_max is None or self.tmp_min is None:  # Initialize on the first data point
            self.tmp_max = high
            self.tmp_min = low
            self.tmp_max_i = index
            self.tmp_min_i = index

        if self.up_zig:  # Looking for a top
            if high > self.tmp_max:
                self.tmp_max = high
                self.tmp_max_i = index
            if high < self.tmp_max - self.sigma:
                self.extremes.loc[self.tmp_max_i] = dict(extreme=self.tmp_max, conf_time=index, type='top')
                self.up_zig = False
                self.tmp_min = low
                self.tmp_min_i = index
        else:  # Looking for a bottom
            if low < self.tmp_min:
                self.tmp_min = low
                self.tmp_min_i = index
            if low > self.tmp_min + self.sigma:
                self.extremes.loc[self.tmp_min_i] = dict(extreme=self.tmp_min, conf_time=index, type='bottom')
                self.up_zig = True
                self.tmp_max = high
                self.tmp_max_i = index

    def get_extremes(self, df, sigma=None):
        if sigma:
            self.sigma = sigma
        self._reset_extremes()
        for index, row in df.iterrows():
            self.process_data_point(index, row['high'], row['low'])
        return self

    def plot(self, ax=None):
        x = self.extremes.index
        y = self.extremes.extreme
        if self.line is None:
            if ax:
                # plot into specified axes
                self.line, = ax.plot(x, y, color='r')
            else:
                # plot into new figure
                self.line, = plt.plot(x, y, color='r')
        else:
            # only update line data if plot already exists
            self.line.set_data((x, y))

    def plotly(self, fig=None, **kwargs):
        x = self.extremes.index
        y = self.extremes.extreme
        if self.line is None:
            if fig:
                fig.add_scatter(x=x, y=y, **kwargs)
        else:
            pass


# TODO: this function doesn't belong here
def plot_data_mpl(df, ax=None, formataxes=True):
    td = df.index[1] - df.index[0]

    for i, (idx, row) in enumerate(df.iterrows()):
        # Vertical line for the high to low range
        ax.plot([idx, idx], [row['low'], row['high']], color='black')
        # Horizontal tick for the open price
        ax.plot([idx - td * 0.1, idx], [row['open'], row['open']], color='black', solid_capstyle='butt', linewidth=2)
        # Horizontal tick for the close price
        ax.plot([idx, idx + td * 0.1], [row['close'], row['close']], color='black', solid_capstyle='butt', linewidth=2)

    if formataxes:
        ax.xaxis.set_major_locator(mdates.HourLocator(0))
        ax.xaxis.set_major_formatter(mdates.DateFormatter(''))
        ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6)))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter(''))
        ax.xaxis.grid(visible=True, which='major', color='k')

        sec = ax.secondary_xaxis(location=-0.075)
        sec.xaxis.set_major_locator(mdates.HourLocator(0))
        sec.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%d.%m'))

        ax.grid('on')

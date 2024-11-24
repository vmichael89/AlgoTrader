import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def dc(df, sigma=0.001):

    extreme_col = f'DC_{sigma}_extreme'
    overshoot_col = f'DC_{sigma}_overshoot'

    def save_overshoot(time=None, val=None):
        """Saves `last_overshoot` at `timestamp` from outer scope if not specified"""
        if not time:
            time = timestamp
        if not val:
            val = last_overshoot
        df.loc[time, overshoot_col] = val

    def save_extreme():
        # get value and index from last saved overshoot event
        extreme_index = df[overshoot_col].dropna().index[-1]
        extreme_value = df[overshoot_col].dropna().iloc[-1]
        # save
        df.loc[extreme_index, extreme_col] = extreme_value
        # df.loc[extreme_index, 'DC_conf_time'] = timestamp

    # Initializations
    df[[extreme_col, overshoot_col]] = pd.NA
    # df['DC_conf_time'] = pd.NaT
    # df['DC_conf_time'] = df['DC_conf_time'].dt.tz_localize('UTC')
    up_zig = False  # tracks if current trend is upwards
    down_zig = False  # tracks if current trend is downwards
    last_overshoot = 0  # compared to current high/low to determine overshoot events
    initial_timestamp = df.index[0]  # only used in trend initialization (while up_zig==down_zig==False)
    initial_high = df['high'].iloc[0]  # only used in trend initialization (while up_zig==down_zig==False)
    initial_low = df['low'].iloc[0]  # only used in trend initialization (while up_zig==down_zig==False)

    # loop through df, omit everything except high and low
    for timestamp, (_, high, low, *_) in df.iterrows():

        # trend initialization / wait for first overshoot event
        if not (up_zig or down_zig):
            if down_zig := low <= initial_high - sigma:
                # save first high as first overshoot and first extreme
                save_overshoot(initial_timestamp, initial_high)
                save_extreme()
                # save time/val from current overshoot event
                last_overshoot = low
                save_overshoot()
            elif up_zig := high >= initial_low + sigma:
                # save first low as first overshoot and first extreme
                save_overshoot(initial_timestamp, initial_low)
                save_extreme()
                # save time/val from current overshoot event
                last_overshoot = high
                save_overshoot()

        elif up_zig:
            if overshoot_event := high > last_overshoot:
                last_overshoot = high
                save_overshoot()
            elif down_zig := low <= last_overshoot - sigma:
                up_zig = False
                save_extreme()
                last_overshoot = low
                save_overshoot()

        elif down_zig:
            if undershoot_event := low < last_overshoot:
                last_overshoot = low
                save_overshoot()
            elif up_zig := high >= last_overshoot + sigma:
                down_zig = False
                save_extreme()
                last_overshoot = high
                save_overshoot()


class DirectionalChange:
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

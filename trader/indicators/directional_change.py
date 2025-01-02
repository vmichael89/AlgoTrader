import pandas as pd

from . import Indicator

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class DirectionalChange(Indicator):
    EXTREME_COL_NAME = 'extreme'
    OVERSHOOT_COL_NAME = 'overshoot'

    def __init__(self, instrument, sigma=0.001, high_colname='high', low_colname='low'):
        self.instrument = instrument  # reference to the underlying data
        self.sigma = sigma
        self.high_colname = high_colname
        self.low_colname = low_colname
        self.overshoots = pd.DataFrame(
            columns=['overshoot', 'type'],
            index=pd.DatetimeIndex([], name='datetime', tz=None))
        self.extremes = pd.DataFrame(
            columns=['extreme', 'conf_time', 'type', 'total_price_movement', 'time_for_completion', 'retracement'],
            index=pd.DatetimeIndex([], name='datetime', tz=None))

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
        if self.overshoots.empty and self.timezone:
            time = time.tz_localize(None)
        self.overshoots.loc[time, self.OVERSHOOT_COL_NAME] = val
        if self.overshoots.index.tz != self.timezone:
            self.overshoots.index = self.overshoots.index.tz_localize(self.timezone)

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
        if self.extremes.empty and self.timezone:
            extreme_index = extreme_index.tz_localize(None)
        self.extremes.loc[extreme_index] = {
            'extreme': extreme_value,
            'conf_time': self.timestamp,
            'type': 'top' if self.down_zig else 'bottom',
            'total_price_movement': total_price_movement,
            'time_for_completion': time_for_completion,
            'retracement': retracement
        }
        if self.extremes.index.tz != self.timezone:
            self.extremes.index = self.extremes.index.tz_localize(self.timezone)

    def get_extremes(self, df):
        # loop through df, omit everything except high and low
        for timestamp, row in df.iterrows():
            self.process_data_point(timestamp, row)

    def process_data_point(self, timestamp, row):
        high = row[self.high_colname]
        low = row[self.low_colname]
        self.timestamp = timestamp
        self.timezone = timestamp.tz

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

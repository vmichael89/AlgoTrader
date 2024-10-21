import os
import re
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from .algos.directional_change import dc


class Data:
    # Define column name constants
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'
    INDEX = 'datetime'

    def __init__(self, symbol, start, end, granularity, price, df):
        self.symbol = symbol
        self.start = start
        self.end = end
        self.granularity = granularity
        self.price = price
        self.df = df
        self.indicators = []  # Not implemented yet

    def __repr__(self):
        sanitized_symbol = re.sub(r'[<>:"/\\|?*]', '_', self.symbol)
        return '.'.join([sanitized_symbol, self.price, self.granularity, self.start, self.end])

    @property
    def default_filename(self):
        return f'./data/{str(self)}.pkl'

    @property
    def num_candles(self):
        return len(self.df)

    @property
    def granularity_value(self):
        multiplier, unit = re.match(r'(\d+)(\w+)', '28D').groups()
        if unit == 'M':
            value = str(int(multiplier) * 30) + 'D'
        elif unit == 'Y':
            value = str(int(multiplier) * 356) + 'D'
        else:
            value = self.granularity
        return pd.to_timedelta(value)

    @staticmethod
    def assert_data_with_same_symbol(data1: 'Data', data2: 'Data'):
        instrument1 = data1.symbol
        instrument2 = data2.symbol
        if instrument1 != instrument2:
            raise Exception(f'Incompatible instruments {instrument1} and {instrument2}.')
        return instrument1

    @staticmethod
    def assert_data_with_same_granularity(data1: 'Data', data2: 'Data'):
        granularity1 = data1.granularity_value
        granularity2 = data2.granularity_value
        if granularity1 != granularity2:
            raise Exception(f'Incompatible granularity {granularity1} and {granularity2}.')
        return granularity1

    def save(self, filepath=None, folderpath=None):
        """Saves data's dataframe in pickle format.

        .save() saves with default file name in the current directory.
        .save(filepath=path_to_file) saves to path_to_file.
        .save(folderpath=path_to_folder) saves with default file name to path_to_folder.

        default file name is str(self).pkl"""

        if folderpath:
            filepath = os.path.join(folderpath, self.default_filename)
        elif not filepath:
            filepath = self.default_filename
        self.df.to_pickle(filepath)
        print(f'{str(self)} saved to {filepath}')

    def load(self):
        self.df = pd.read_pickle(self.default_filename)
        return self

    def add_candle(self, time, o, h, l, c, volume):
        self.df = pd.concat([
            self.df,
            pd.DataFrame(data={'open': o, 'high': h, 'low': l, 'close': c, 'volume': volume}, index=[time])
        ])

    def add_indicator(self, indicator, *args, **kwargs):
        """Add a TALib-alike indicator in the form of (function, kwargs of the function)."""
        if indicator == 'dc':
            # use trader library
            self.df['DC'] = dc(self.df['high'], self.df['low'], *args, **kwargs)
        else:
            # use ta library
            self.df.ta(kind=indicator, *args, **kwargs, append=True)

    def plot_data(self):
        graph_obj = go.Candlestick(
            name=str(self),
            x=self.df.index,
            open=self.df.open,
            high=self.df.high,
            low=self.df.low,
            close=self.df.close,
            increasing_line_color='black',
            decreasing_line_color='black',
            increasing_fillcolor='lightblue',
            decreasing_fillcolor='gray',
            increasing_line_width=0.5,
            decreasing_line_width=0.5
        )
        return graph_obj

    def plot_indicator(self):
        graph_objs = []
        for col in self.df.columns:
            if col in [Data.OPEN, Data.HIGH, Data.LOW, Data.CLOSE, Data.VOLUME, 'complete']:
                continue
            data = self.df[col].dropna()
            graph_objs.append(
                go.Scatter(
                    name=col,
                    x=data.index,
                    y=data.values,
                    mode='lines' if len(data.value_counts()) > 3 else 'markers'
                )
            )
        return graph_objs

    def plot(self):
        fig = go.Figure(data=[self.plot_data(), *self.plot_indicator()])
        fig.update_layout(xaxis_rangeslider_visible=False)
        fig.show(renderer='browser')

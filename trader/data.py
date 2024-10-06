import os
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go


class Data:
    def __init__(self, symbol, start, end, granularity, price, df):
        self.symbol = symbol
        self.start = start
        self.end = end
        self.granularity = granularity
        self.price = price
        self.df = df
        self.indicators = []  # Not implemented yet

    def __repr__(self):
        return '.'.join([self.symbol, self.price, self.granularity, self.start, self.end])

    @property
    def default_filename(self):
        return f'{str(self)}.pkl'

    @property
    def num_candles(self):
        return len(self.df)

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

    def add_indicator(self):
        pass

    def plot(self):
        fig = go.Figure(data=[go.Candlestick(x=self.df.index, open=self.df.open, high=self.df.high, low=self.df.low, close=self.df.close)])
        fig.update_layout(title=str(self), xaxis_rangeslider_visible=False)
        return fig

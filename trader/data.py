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
        return f'./data/{str(self)}.pkl'

    @property
    def num_candles(self):
        return len(self.df)

    @staticmethod
    def assert_data_with_same_symbol(data1: 'Data', data2: 'Data'):
        instrument1 = data1.symbol
        instrument2 = data2.symbol
        if instrument1 != instrument2:
            raise Exception(f'Incompatible instruments {instrument1} and {instrument2}.')
        return instrument1

    @staticmethod
    def assert_data_with_same_granularity(data1: 'Data', data2: 'Data'):
        # Get granularities from most occurring time difference
        granularity1 = data1.get_most_occurring_granularity()
        granularity2 = data2.get_most_occurring_granularity()
        if granularity1 != granularity2:
            raise Exception(f'Incompatible granularity {granularity1} and {granularity2}.')
        return granularity1

    def get_most_occurring_granularity(self):
        return self.df.index.to_series().diff().value_counts().index[0]

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

    def plot(self):
        fig = go.Figure(data=self.plot_data())
        fig.update_layout(xaxis_rangeslider_visible=False)
        fig.show(renderer='browser')

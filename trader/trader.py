import os
import datetime

import plotly.graph_objects as go

from .broker import OandaBroker
from .data import Data


class Trader:

    def __init__(self):
        self.broker = OandaBroker()
        self.data = []

    def add_data(self, instruments, **kwargs):
        today = datetime.datetime.utcnow().date().strftime('%Y-%m-%d')
        seven_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).date().strftime('%Y-%m-%d')

        start = kwargs.get('start', seven_days_ago)
        end = kwargs.get('end', today)
        granularity = kwargs.get('granularity', 'H1')
        price = kwargs.get('price', 'M')

        # Check if data is locally available
        for instrument in instruments:
            for p in price:
                dummy_data = Data(symbol=instrument, start=start, end=end, granularity=granularity, price=p, df=[])
                if os.path.exists(str(dummy_data) + '.pkl'):
                    print(f'Loading from file: {instrument} data from {start} to {end} with granularity {granularity} and price {p}')
                    self.data.append(dummy_data.load())
                else:
                    print(f'Fetching from broker: {instruments} data from {start} to {end} with granularity {granularity} and price {p}')
                    self.data.extend(self.broker.get_data(instrument, start, end, granularity, p))

    def remove_data(self, index):
        data = self.data.pop(index)
        print(f'Removed {data}')

    def save_data(self, save_all=False, data: Data = None, indices=None):
        """Save specific Data to file.

        .save_data(save_all=True) to save all data.
        .save_data(data=data_obj) to save only selected data.
        .save_data(indices=[0,2] to save traders 0th and 2nd data object."""

        if save_all:
            for data in self.data:
                data.save()

        elif indices:
            for i in indices:
                self.data[i].save()

        elif data:
            data.save()

    def plot_bid_ask_candles(self, bid: int, ask: int):
        """Creates a plot with bid and ask candles.

        Parameters
        ----------
        bid: trader's data index of bid data
        ask: trader's data index of ask data"""

        bid_data = self.data[bid]
        ask_data = self.data[ask]

        bid_instrument = bid_data.symbol
        ask_instrument = ask_data.symbol
        if bid_instrument != ask_instrument:
            raise Exception(f'Incompatible instruments {bid_instrument} and {ask_instrument}.')

        # Get granularities from most occurring time difference
        bid_granularity = bid_data.df.index.to_series().diff().value_counts().index[0]
        ask_granularity = ask_data.df.index.to_series().diff().value_counts().index[0]
        if bid_granularity != ask_granularity:
            raise Exception(f'Incompatible granularity {bid_granularity} and {ask_granularity}.')

        # Initialize figure
        fig = go.Figure(data=[bid_data.plot_data(), ask_data.plot_data()])
        fig.update_layout(xaxis_rangeslider_visible=False)

        # Modify figure: shift-left bid candles and shift-right ask candles
        td = bid_granularity / 8
        adjusted_bid_index = bid_data.df.index - td
        adjusted_ask_index = ask_data.df.index + td
        fig.data[0].x = adjusted_bid_index
        fig.data[1].x = adjusted_ask_index

        fig.show(renderer='browser')

    def plot_dual_timeframe(self):
        pass

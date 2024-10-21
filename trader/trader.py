import os
import datetime
import itertools
import pandas as pd

import plotly.graph_objects as go

from .broker import OandaBroker, PolygonAPI
from .data import Data


class Trader:

    broker_names = {'oanda': OandaBroker, 'polygon': PolygonAPI}

    def __init__(self):
        self.brokers = {}
        self.data = []

    def add_broker(self, broker):
        # Check if `broker` is in implemented broker_names
        if broker in self.broker_names:
            self.brokers[broker] = self.broker_names[broker]()  # Create broker instance
        else:
            available_brokers = ', '.join(cls.__name__ for cls in self.broker_names.values())
            raise KeyError(f'`{broker}` not available in brokers: {available_brokers}')

    def add_data(self, instruments, start=None, end=None, granularities='1H', prices='M', broker=None):

        today = datetime.datetime.utcnow().date().strftime('%Y-%m-%d')
        seven_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).date().strftime('%Y-%m-%d')

        # Default values
        start = seven_days_ago if not start else start
        end = today if not end else end

        # Force to lists
        instruments = [instruments] if not isinstance(instruments, list) else instruments
        granularities = [granularities] if not isinstance(granularities, list) else granularities
        prices = [prices] if not isinstance(prices, list) else prices

        # Select a broker, default to the first one in the dictionary if not specified
        if broker is None:
            if len(self.brokers) == 0:
                broker_instance = None
            else:
                broker = next(iter(self.brokers.keys()))  # Get the first broker if none is specified
                broker_instance = self.brokers[broker]
        elif broker in self.brokers:
            broker_instance = self.brokers[broker]
        else:
            raise KeyError(f'`{broker}` broker not available.')

        # Check if data is locally available
        for instrument, granularity, price in itertools.product(instruments, granularities, prices):
            dummy_data = Data(symbol=instrument, start=start, end=end, granularity=granularity, price=price, df=[])
            if os.path.exists(dummy_data.default_filename):
                print(f'Loading from file: {instrument} data from {start} to {end} with granularity {granularity} and price {price}')
                self.data.append(dummy_data.load())
            else:
                print(f'Fetching from {broker}: {instrument} data from {start} to {end} with granularity {granularity} and price {price}')
                if broker_instance:
                    self.data.append(broker_instance.get_data(instrument, start, end, granularity, price))
                else:
                    raise ValueError("No broker instance added. Please add a broker using `.add_broker()`")

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

    def add_indicator(self, indicator, *args, **kwargs):
        """Add a TALib-alike indicator in the form of (function, kwargs of the function)."""
        for data in self.data:
            data.add_indicator(indicator, *args, **kwargs)

    def plot_bid_ask_candles(self, bid: int, ask: int, equal_instruments=True):
        """Creates a plot with bid and ask candles.

        Parameters
        ----------
        bid: trader's data index of bid data
        ask: trader's data index of ask data"""

        bid_data: Data = self.data[bid]
        ask_data: Data = self.data[ask]

        if equal_instruments:
            Data.assert_data_with_same_symbol(bid_data, ask_data)

        granularity_val = Data.assert_data_with_same_granularity(bid_data, ask_data)

        # Initialize figure
        fig = go.Figure(data=[bid_data.plot_data(), ask_data.plot_data()])
        fig.update_layout(xaxis_rangeslider_visible=False)

        # Modify figure: shift-left bid candles and shift-right ask candles
        td = granularity_val / 8
        adjusted_bid_index = bid_data.df.index - td
        adjusted_ask_index = ask_data.df.index + td
        fig.data[0].x = adjusted_bid_index
        fig.data[1].x = adjusted_ask_index

        fig.show(renderer='browser')

    def plot_dual_timeframe(self, low_timeframe: int, high_timeframe: int):
        """Creates a plot with bid and ask candles.

        Parameters
        ----------
        low_timeframe: trader's data index of lower timeframe data, e.g. hourly
        high_timeframe: trader's data index of higher timeframe data, e.g. daily"""

        high_gran_data: Data = self.data[low_timeframe]
        low_gran_data: Data = self.data[high_timeframe]

        Data.assert_data_with_same_symbol(low_gran_data, high_gran_data)

        low_granularity = low_gran_data.granularity_value
        high_granularity = high_gran_data.granularity_value

        # Initialize figure
        fig = go.Figure(data=[low_gran_data.plot_data(), high_gran_data.plot_data()],
                        layout=dict(
                            xaxis=dict(
                                rangeslider_visible=False,
                                showgrid=True,
                                gridcolor='lightgray',  # Set grid color to ensure it's visible
                                gridwidth=1,
                                tickvals=pd.date_range(  # Ticks between big candles
                                    start=low_gran_data.df.index.min() - low_granularity / 2,
                                    end=low_gran_data.df.index.max() + low_granularity / 2,
                                    freq=low_granularity)
                                # TODO tick handling needs to be be done better
                                #  not good lowgran data is hidden
                            ),
                            xaxis2=dict(
                                rangeslider_visible=False,
                                overlaying='x',
                                side='bottom',
                                dtick='H1'
                            ),
                            hovermode='x unified'
                        ))
        fig.update_traces(selector=dict(name=str(high_gran_data)), xaxis='x2')
        fig.show(renderer='browser')

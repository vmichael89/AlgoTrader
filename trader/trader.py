import os
import datetime
import itertools
import pandas as pd
import plotly.graph_objects as go
from .broker import Broker, OandaBroker, PolygonAPI, MetaTrader
from .data import Data
import threading


class Trader:

    broker_names = {'mt5': MetaTrader, 'oanda': OandaBroker, 'polygon': PolygonAPI}

    def __init__(self):
        self.brokers = {}
        self.broker = None
        self.data = []
        self.indicators = []
        self.strategies = []
        self.positions = []
        self.data_streams = []
        self.stop_event = threading.Event()

    def add_broker(self, broker):
        if self.broker:
            raise ValueError("Broker instance already added.")
        else:
            # Check if `broker` is in implemented broker_names
            if broker in self.broker_names:
                self.brokers[broker] = self.broker_names[broker]()  # Create broker instance
                self.broker = self.broker_names[broker]()
                self.broker.trader = self
            else:
                available_brokers = ', '.join(cls.__name__ for cls in self.broker_names.values())
                raise KeyError(f'`{broker}` not available in brokers: {available_brokers}')

    def add_data(self, instruments, start=None, end=None, granularities='1H', prices='M', days=7):

        today = datetime.datetime.utcnow().isoformat() + 'Z'
        seven_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).date().strftime('%Y-%m-%d')

        # Default values
        start = seven_days_ago if not start else start
        end = today if not end else end

        # Force to lists
        instruments = [instruments] if not isinstance(instruments, list) else instruments
        granularities = [granularities] if not isinstance(granularities, list) else granularities
        prices = [prices] if not isinstance(prices, list) else prices

        # Check if data is locally available
        for instrument, granularity, price in itertools.product(instruments, granularities, prices):
            dummy_data = Data(symbol=instrument, start=start, end=end, granularity=granularity, price=price, df=[])
            if os.path.exists(dummy_data.default_filename):
                print(f'Loading from file: {instrument} data from {start} to {end} with granularity {granularity} and price {price}')
                self.data.append(dummy_data.load())
            else:
                print(f'Fetching from {self.broker}: {instrument} data from {start} to {end} with granularity {granularity} and price {price}')
                if granularity == 'tick':
                    self.data.append(self.broker.get_tick_data(instrument, start, end))
                else:
                    self.data.append(self.broker.get_data(instrument, start, end, granularity, price))

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

    def add_indicator(self, instrument, indicator, params: dict):
        self.indicators.append(indicator(instrument, **params))

    def market_order(self, instrument, order_size, sl=None, tp=None, magic=0, comment=""):
        position = self.broker.market_order(
            instrument=instrument, order_size=order_size, sl=sl, tp=tp, magic=magic, comment=comment)
        self.positions.append(position)
        return position

    def change_position_sltp(self, position, sl=None, tp=None, magic=0, comment=""):
        position = self.broker.change_position_sltp(
            position=position, sl=sl, tp=tp, magic=magic, comment=comment)
        self.positions.append(position)
        return position

    def close_position(self, position, volume=None):
        return self.broker.close_position(position)

    def close_all_positions(self, instrument=None, group="*"):
        self.broker.close_all_positions(instrument=instrument, group=group)

    def get_positions(self, as_dataframe=True):
        return self.broker.get_positions(as_dataframe=as_dataframe)

    def get_trades(self, as_dataframe=True):
        return self.broker.get_trades(as_dataframe=as_dataframe)

    def add_strategy(self, strategy):
        strategy.trader = self
        self.strategies.append(strategy)

    def backtest(self):
        # Loop through data, update indicators, and run strategies
        pass

    def add_data_stream(self, instrument, frequency=1):
        """Add a data stream for the specified instrument."""
        if self.broker:
            self.data_streams.append([instrument, frequency, 0])
        else:
            raise ValueError("Broker instance must be added before adding data streams.")

    def run_live(self):
        """Start all data streams in parallel."""
        if not self.data_streams:
            raise ValueError("No data streams added. Use add_data_stream to add streams.")
        
        def start_stream(instrument, frequency):
            while not self.stop_event.is_set():
                self.broker.stream_tick_data(instrument, frequency)
        
        threads = []
        for instrument, frequency, _ in self.data_streams:
            thread = threading.Thread(target=start_stream, args=(instrument, frequency))
            thread.daemon = True  # Make the thread a daemon so it exits when the main program exits
            threads.append(thread)
            thread.start()
        
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            self.stop_event.set()
            print("Stopping all data streams...")

    def stop_live(self):
        """Stop all data streams."""
        self.stop_event.set()
        print("All data streams stopped.")

    def on_new_data(self, instrument, frequency, data: pd.DataFrame):
        for index, row in data.itterrows():
            # Update indicators
            for indicator in self.indicators:
                indicator.process_data_point(row)

            # Step through strategies
            for strategy in self.strategies:
                if instrument in strategy.instruments:
                    strategy.on_new_data(row)

    def plot(self):
        figs = [data.plot() for data in self.data]
        return figs

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
        return fig

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
        return fig
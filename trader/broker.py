from abc import ABC, abstractmethod
from pathlib import Path
import threading

import pandas as pd
import tpqoa


# Inherit standard api class to change streaming behavior
class OandaAPI(tpqoa.tpqoa):
    def on_success(self, time, instrument, bid, ask):
        """Method called when new data is retrieved."""
        print(time, instrument, bid, ask)

    def stream_data(self, instrument, stop=None, ret=False, callback=None):
        """Starts a real-time data stream.

        Parameters
        ==========
        instrument: string
            valid instrument name
        """
        self.stream_instrument = instrument
        self.ticks = 0
        response = self.ctx_stream.pricing.stream(
            self.account_id, snapshot=True,
            instruments=instrument)
        msgs = []
        for msg_type, msg in response.parts():
            msgs.append(msg)
            # print(msg_type, msg)
            if msg_type == 'pricing.ClientPrice':
                self.ticks += 1
                self.time = msg.time
                if callback is not None:
                    callback(msg.instrument, msg.time,
                             float(msg.bids[0].dict()['price']),
                             float(msg.asks[0].dict()['price']))
                else:
                    self.on_success(msg.time,
                                    msg.instrument,
                                    float(msg.bids[0].dict()['price']),
                                    float(msg.asks[0].dict()['price']))
                if stop is not None:
                    if self.ticks >= stop:
                        if ret:
                            return msgs
                        break
            if self.stop_stream:
                if ret:
                    return msgs
                break

    def start_stream(self, instruments):
        """Start streaming prices for all instruments in separate threads."""
        thread = threading.Thread(target=self.stream_data, args=(instruments,))
        thread.daemon = True  # Make the thread a daemon so it exits when the main program exits
        thread.start()
        # self.stream_threads[instruments] = thread
        print(f'Started streaming for {instruments}')


class Data:
    def __init__(self, symbol, start, end, granularity, price, df):
        self.symbol = symbol
        self.start = start
        self.end = end
        self.granularity = granularity
        self.price = price
        self.df = df
        self.candles = len(df)

    def __repr__(self):
        return ','.join([self.symbol, self.price, self.granularity, f'{self.candles} candles'])

    def add_candle(self, time, o, h, l, c, volume):
        self.df = pd.concat([
            self.df,
            pd.DataFrame(data={'open': o, 'high': h, 'low': l, 'close': c, 'volume': volume}, index=[time])
        ])


class Broker(ABC):

    @abstractmethod
    def get_data(self, instruments, start, end, granularity, price, log=False):
        pass


class OandaBroker(Broker):
    def __init__(self):
        self.api = OandaAPI((Path('.') / 'config' / 'oanda.cfg').resolve().__str__())
        self.instruments = type('Instruments', (object,), {instr[1]: instr[1] for instr in self.api.get_instruments()})()

    def get_data(self, instruments, start, end, granularity, price, log=False):
        """
        Fetch historical data for the specified instruments from Oanda.

        :param instruments: List of instruments (e.g., ['EUR_USD', 'GBP_USD'])
        :param start: Start date for the historical data (e.g., '2024-07-29')
        :param end: End date for the historical data (e.g., '2024-08-20')
        :param granularity: Time interval for data (e.g., 'H1' for 1-hour candles)
        :param price: Price type ('M' for mid prices)
        :param log: Whether to log the progress of fetching data (default: False)
        :return: Dictionary of dataframes, each corresponding to one instrument
        """

        if isinstance(instruments, str):
            instruments = [instruments]

        datas = []

        for instr in instruments:
            if log:
                print(f'Fetching data for {instr}...')

            # Get historical data for the instrument
            df_data = self.api.get_history(
                instrument=instr,
                start=start,
                end=end,
                granularity=granularity,
                price=price,
                localize=False
            )

            # Rename columns
            df_data = df_data.rename(
                columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'volume': 'Volume'}
            )

            data = Data(instr, start, end, granularity, price, df_data)

            datas.append(data)

        return datas

    def stream_data(self, instrument):
        self.api.stream_data(instrument)

from abc import ABC, abstractmethod
from pathlib import Path
import threading
import json
import requests

import pandas as pd
import tpqoa

from .data import Data


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


class Broker(ABC):

    @property
    @abstractmethod
    def COLUMN_MAPPING(self):
        """Must return a dictionary for column mapping."""
        pass

    @property
    @abstractmethod
    def GRANULARITY_MAP(self):
        """Must return a dictionary for granularity mapping."""
        pass

    @classmethod
    def __repr__(cls):
        return cls.__class__.__name__  # Returns the class name

    @abstractmethod
    def get_data(self, instruments, start, end, granularity, price):
        pass


class OandaBroker(Broker):

    @property
    def COLUMN_MAPPING(self):
        return {
            'o': Data.OPEN,
            'h': Data.HIGH,
            'l': Data.LOW,
            'c': Data.CLOSE,
            'volume': Data.VOLUME
        }

    @property
    def GRANULARITY_MAP(self):
        return {
            pd.to_timedelta('5S'): 'S5',
            pd.to_timedelta('10S'): 'S10',
            pd.to_timedelta('15S'): 'S15',
            pd.to_timedelta('30S'): 'S30',
            pd.to_timedelta('1min'): 'M1',
            pd.to_timedelta('2min'): 'M2',
            pd.to_timedelta('4min'): 'M4',
            pd.to_timedelta('5min'): 'M5',
            pd.to_timedelta('10min'): 'M10',
            pd.to_timedelta('15min'): 'M15',
            pd.to_timedelta('30min'): 'M30',
            pd.to_timedelta('1H'): 'H1',
            pd.to_timedelta('2H'): 'H2',
            pd.to_timedelta('3H'): 'H3',
            pd.to_timedelta('4H'): 'H4',
            pd.to_timedelta('6H'): 'H6',
            pd.to_timedelta('8H'): 'H8',
            pd.to_timedelta('12H'): 'H12',
            pd.to_timedelta('1D'): 'D',
            pd.to_timedelta('1W'): 'W',
            pd.to_timedelta('1M'): 'M'
        }

    def __init__(self):
        self.api = OandaAPI((Path('.') / 'config' / 'oanda.cfg').resolve().__str__())
        self.instruments = type('Instruments', (object,), {instr[1]: instr[1] for instr in self.api.get_instruments()})()

    def get_data(self, instruments, start, end, granularity, price):
        """
        Fetch historical data for the specified instruments from Oanda.

        :param instruments: List of instruments (e.g., ['EUR_USD', 'GBP_USD'])
        :param start: Start date for the historical data (e.g., '2024-07-29')
        :param end: End date for the historical data (e.g., '2024-08-20')
        :param granularity: Time interval for data (e.g., 'H1' for 1-hour candles)
        :param price: Price type ('M' for mid prices)
        :return: Dictionary of dataframes, each corresponding to one instrument
        """

        if isinstance(instruments, str):
            instruments = [instruments]

        # Check if granularity is in the map, if not raise an error
        granularity_timedelta = pd.to_timedelta(granularity)
        if granularity_timedelta not in self.GRANULARITY_MAP:
            raise ValueError(f"Granularity {granularity} is not valid or not supported.")

        datas = []

        for instr in instruments:

            # Get historical data for the instrument
            df_data = self.api.get_history(
                instrument=instr,
                start=start,
                end=end,
                granularity=self.GRANULARITY_MAP[granularity_timedelta],
                price=price,
                localize=False
            )

            # Rename columns
            df_data = df_data.rename(columns=self.COLUMN_MAPPING)
            df_data.index.name = Data.INDEX

            data = Data(instr, start, end, granularity_timedelta, price, df_data)

            datas.append(data)

        return datas

    def stream_data(self, instrument):
        self.api.stream_data(instrument)


class PolygonAPI(Broker):
    def __init__(self):
        with open(Path('.') / 'config' / 'polygon.cfg', 'r') as f:
            self.API_KEY = f.read()

    def get_data(self, instruments, start, end, granularity, price='M', log=False):
        headers = {"Authorization": "Bearer " + self.API_KEY}

        datas = {}

        for instrument in instruments:
            print(f"Fetching data for {instrument}")

            data = []

            url = f'https://api.polygon.io/v2/aggs/ticker/{instrument}/range/{granularity[0]}/{granularity[1]}/{start}/{end}?adjusted=true&sort=asc&limit=50000&apiKey={self.API_KEY}'
            while True:
                aggs = json.loads(requests.get(url, headers=headers).text)

                if aggs["resultsCount"] == 0:
                    break

                data.extend(aggs['results'])

                if "next_url" in aggs:
                    url = aggs["next_url"]
                else:
                    break

            df = pd.DataFrame(data)

            df.drop(columns=['vw', 'n'], inplace=True)
            df.rename(columns={'o': 'open', 'c': 'close', 'h': 'high', 'l': 'low', 'v': 'volume', 't': 'date'},
                      inplace=True)
            df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            df.set_index('datetime', inplace=True)

            # if timezone=="new york":
            df.index = df.index.tz_localize('UTC')
            df.index = df.index.tz_convert('America/New_York')
            df.index = df.index.tz_localize(None)

            datas[instrument] = df

        return datas

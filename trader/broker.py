from abc import ABC, abstractmethod
from pathlib import Path
import threading
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

    @classmethod
    def __repr__(cls):
        return cls.__class__.__name__  # Returns the class name

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

    @abstractmethod
    def _fetch_broker_data(self, instrument, start, end, granularity, price):
        """
        Broker-specific method to fetch raw data from the broker's API.
        Must return a dataframe with OHLC values and a datetime index.
        """
        pass

    def get_data(self, instrument, start, end, granularity, price):
        """Fetch and transform historical data for the specified instruments."""

        # Convert granularity to timedelta
        if granularity not in self.GRANULARITY_MAP:
            raise ValueError(f"Granularity {granularity} is not valid or not supported.")

        # Fetch broker-specific data
        df_data = self._fetch_broker_data(instrument, start, end, granularity, price)

        # Rename columns using the shared mapping
        df_data = df_data.rename(columns=self.COLUMN_MAPPING)
        df_data.index.name = Data.INDEX

        # Wrap the transformed data in the Data class
        data = Data(instrument, start, end, granularity, price, df_data)

        return data


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
            '5S': 'S5',
            '10S': 'S10',
            '15S': 'S15',
            '30S': 'S30',
            '1min': 'M1',
            '2min': 'M2',
            '4min': 'M4',
            '5min': 'M5',
            '10min': 'M10',
            '15min': 'M15',
            '30min': 'M30',
            '1H': 'H1',
            '2H': 'H2',
            '3H': 'H3',
            '4H': 'H4',
            '6H': 'H6',
            '8H': 'H8',
            '12H': 'H12',
            '1D': 'D',
            '1W': 'W',
            '1M': 'M'
        }

    def __init__(self):
        self.api = OandaAPI((Path('.') / 'config' / 'oanda.cfg').resolve().__str__())
        self.instruments = type('Instruments', (object,), {instr[1]: instr[1] for instr in self.api.get_instruments()})()

    def _fetch_broker_data(self, instrument, start, end, granularity, price):
        return self.api.get_history(
            instrument=instrument,
            start=start,
            end=end,
            granularity=self.GRANULARITY_MAP[granularity],
            price=price,
            localize=False
        )

    def stream_data(self, instrument):
        self.api.stream_data(instrument)


class PolygonAPI(Broker):

    @property
    def COLUMN_MAPPING(self):
        return {
            'o': Data.OPEN,
            'h': Data.HIGH,
            'l': Data.LOW,
            'c': Data.CLOSE,
            'v': Data.VOLUME,
        }

    @property
    def GRANULARITY_MAP(self):
        return {
            '5S': ('second', 1),
            '10S': ('second', 10),
            '15S': ('second', 15),
            '30S': ('second', 30),
            '1min': ('minute', 1),
            '2min': ('minute', 2),
            '4min': ('minute', 4),
            '5min': ('minute', 5),
            '10min': ('minute', 10),
            '15min': ('minute', 15),
            '30min': ('minute', 30),
            '1H': ('hour', 1),
            '2H': ('hour', 2),
            '3H': ('hour', 3),
            '4H': ('hour', 4),
            '6H': ('hour', 6),
            '8H': ('hour', 8),
            '12H': ('hour', 12),
            '1D': ('day', 1),
            '1W': ('week', 1),
            '1M': ('month', 1),
            '3M': ('month', 3),
            '4M': ('month', 4),
            '6M': ('month', 6),
            '1Y': ('year', 1),
            '5Y': ('year', 5),
        }

    def __init__(self):
        with open(Path('.') / 'config' / 'polygon.cfg', 'r') as f:
            self.API_KEY = f.read()

        self.HEADERS = {"Authorization": "Bearer " + self.API_KEY}

        self.tickers_api = (
            lambda instrument:
            f'https://api.polygon.io/v3/reference/tickers?ticker={instrument}'
        )

        self.aggregates_api = (
            lambda instrument, granularity_value, granularity_type, start, end:
            f'https://api.polygon.io/v2/aggs/ticker/{instrument}/range/{granularity_value}'
            f'/{granularity_type}/{start}/{end}?adjusted=true&sort=asc&limit=50000'
        )

    def _request(self, url):
        """Polygon-specific wrapper to request all data."""
        data = []
        while True:
            response = requests.get(url=url, headers=self.HEADERS)
            aggs = response.json()
            data.extend(aggs['results'])
            if "next_url" in aggs:
                url = aggs["next_url"]
            else:
                return data

    def _fetch_broker_data(self, instrument, start, end, granularity, price='M'):

        granularity_type, granularity_value = self.GRANULARITY_MAP[granularity]

        # Check if instrument is valid
        tickers_url = self.tickers_api(instrument)
        tickers_data = self._request(tickers_url)
        if len(tickers_data) == 0:
            raise ValueError(f"Instrument '{instrument}' is not valid.")

        # Get aggregates (bars/candles) and create a dataframe
        agg_url = self.aggregates_api(instrument, granularity_value, granularity_type, start, end)
        agg_data = self._request(agg_url)
        df = pd.DataFrame(agg_data)
        df['t'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('t', inplace=True)

        # if timezone=="new york":
        # df.index = df.index.tz_localize('UTC')
        # df.index = df.index.tz_convert('America/New_York')
        # df.index = df.index.tz_localize(None)

        return df

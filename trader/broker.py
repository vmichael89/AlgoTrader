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
                columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'volume': 'volume'}
            )
            df_data.index.name = 'datetime'

            data = Data(instr, start, end, granularity, price, df_data)

            datas.append(data)

        return datas

    def stream_data(self, instrument):
        self.api.stream_data(instrument)


class PolygonAPI():
    def __init__(self):
        with open(Path('.') / 'config' / 'polygon.cfg', 'r') as f:
            self.API_KEY = f.read()

    def get_data(self, instruments, start, end, granularity, timezone="new york"):
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

            if timezone=="new york":
                df.index = df.index.tz_localize('UTC')
                df.index = df.index.tz_convert('America/New_York')
                df.index = df.index.tz_localize(None)

            datas[instrument] = df

        return datas

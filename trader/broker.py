from abc import ABC, abstractmethod
from pathlib import Path
import threading
import requests
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
import tpqoa

from .data import Data, TickData


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
    trader = None

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

    def _fetch_broker_data(self, instrument, start, end, granularity, price):
        """
        Broker-specific method to fetch raw data from the broker's API.
        Must return a dataframe with OHLC values and a datetime index.
        """
        raise NotImplementedError()

    def _fetch_broker_tick_data(self, instrument, start, end):
        raise NotImplementedError()

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

    def get_tick_data(self, instrument, start, end):
        df_data = self._fetch_broker_tick_data(instrument, start, end)
        data = TickData(instrument, start, end, "tick", "BA", df_data)
        return data
    
    def stream_tick_data(self, instrument, frequency=1):
        """Stream real-time data for the specified instrument."""
        raise NotImplementedError()

    def market_order(self, instrument, order_size, sl=None, tp=None, magic=0, comment=""):
        raise NotImplementedError()

    def change_position_sltp(self, position, sl, tp, magic=0, comment=""):
        raise NotImplementedError()

    def close_position(self, position, volume=None, magic=0, comment=""):
        raise NotImplementedError()

    def close_all_positions(self, symbol=None, group="*"):
        raise NotImplementedError()

    def get_positions(self, as_dataframe=True):
        raise NotImplementedError()

    def get_trades(self, as_dataframe=True):
        raise NotImplementedError()


class MetaTrader(Broker):
    FTMO_TIME_ZONE = timezone(timedelta(hours=2))

    @property
    def COLUMN_MAPPING(self):
        return {}

    @property
    def GRANULARITY_MAP(self):
        return {
            '1min': self.api.TIMEFRAME_M1,
            '2min': self.api.TIMEFRAME_M2,
            '3min': self.api.TIMEFRAME_M3,
            '4min': self.api.TIMEFRAME_M4,
            '5min': self.api.TIMEFRAME_M5,
            '6min': self.api.TIMEFRAME_M6,
            '10min': self.api.TIMEFRAME_M10,
            '12min': self.api.TIMEFRAME_M12,
            '15min': self.api.TIMEFRAME_M15,
            '20min': self.api.TIMEFRAME_M20,
            '30min': self.api.TIMEFRAME_M30,
            '1H': self.api.TIMEFRAME_H1,
            '2H': self.api.TIMEFRAME_H2,
            '3H': self.api.TIMEFRAME_H3,
            '4H': self.api.TIMEFRAME_H4,
            '6H': self.api.TIMEFRAME_H6,
            '8H': self.api.TIMEFRAME_H8,
            '12H': self.api.TIMEFRAME_H12,
            '1D': self.api.TIMEFRAME_D1,
            '1W': self.api.TIMEFRAME_W1,
            '1M': self.api.TIMEFRAME_MN1
        }

    def __init__(self, user="FTMO_DEMO"):
        import os
        import MetaTrader5 as mt5

        self.api = mt5
        mt5.initialize()
        login = os.environ[f"{user}_LOGIN"]
        password = os.environ[f"{user}_PASSWORD"]
        server = os.environ[f"{user}_SERVER"]
        mt5.login(login=login, password=password, server=server)
        if not mt5.account_info():
            raise Exception(f"Failed to connect to MetaTrader 5: {mt5.last_error()}")

    def _isoformat_to_ftmo_time(self, isoformat_time):
        # FTMO time (GMT+2) has to be a datetime object without timezone info.
        as_datetime = datetime.fromisoformat(isoformat_time)#.replace(tzinfo=timezone.utc)
        ftmo_time = as_datetime.astimezone(self.FTMO_TIME_ZONE)
        ftmo_time = ftmo_time.replace(tzinfo=timezone.utc)
        return ftmo_time

    def _fetch_broker_data(self, instrument, start, end, granularity, price):
        start_time = self._isoformat_to_ftmo_time(start)
        end_time = self._isoformat_to_ftmo_time(end) if end else self._isoformat_to_ftmo_time(datetime.now().isoformat())

        # Get the number of candles to fetch
        if granularity in self.GRANULARITY_MAP:
            period = self.GRANULARITY_MAP[granularity]
        else:
            raise ValueError(f"Granularity {granularity} is not valid or not supported.")

        # Get the data
        df_data = self.api.copy_rates_range(instrument, period, start_time, end_time)
        df_data = pd.DataFrame(df_data)
        df_data['datetime'] = pd.to_datetime(df_data['time'], unit='s')
        df_data['datetime'] = df_data['datetime'].dt.tz_localize('Etc/GMT-3')
        df_data.set_index('datetime', inplace=True)

        if price == 'B':
            pass
        elif price == 'A':
            point_value = self.api.symbol_info(instrument).point
            for col in ['open', 'high', 'low', 'close']:
                df_data[col] = df_data[col] + df_data['spread'] * point_value

        df_data.drop(columns=['time', 'real_volume', 'spread'], inplace=True)
        return df_data

    def _fetch_broker_tick_data(self, instrument, start, end=None):
        start_time = self._isoformat_to_ftmo_time(start)
        end_time = self._isoformat_to_ftmo_time(end) if end else self._isoformat_to_ftmo_time(datetime.now().isoformat())

        ticks = self.api.copy_ticks_range(instrument, start_time, end_time, self.api.COPY_TICKS_ALL)
        df_ticks = pd.DataFrame(ticks)
        df_ticks['datetime'] = pd.to_datetime(df_ticks['time_msc'], unit='ms')
        df_ticks['datetime'] = df_ticks['datetime'].dt.tz_localize('Etc/GMT-3')
        df_ticks.set_index('datetime', inplace=True)

        df_ticks.drop(columns=['time', 'last', 'time_msc', 'flags', 'volume_real'], inplace=True)
        return df_ticks
    
    def stream_tick_data(self, instrument, frequency=1):
        start_time = datetime.now().isoformat()
        old_ticks = None
        while not self.trader.stop_event.is_set():
            df_ticks = self._fetch_broker_tick_data(instrument, start_time)
            if (not df_ticks.empty) and (old_ticks is not None):
                df_ticks = df_ticks.loc[~df_ticks.index.isin(old_ticks.index)]
            if not df_ticks.empty:
                old_ticks = df_ticks
                start_time = df_ticks.index[-1].isoformat()
                self.trader.on_new_data(instrument, frequency, df_ticks)
            time.sleep(frequency)

    def _order_send(self, action, magic=None, order=None, symbol=None, volume=None, price=None, stoplimit=None, sl=None,
                    tp=None, deviation=None, type=None, type_filling=None, type_time=None, expiration=None, comment="",
                    position=None, position_by=None):
        request = {
            key: value
            for key, value in locals().items()
            if value is not None
        }
        order_result = self.api.order_send(request)

        if order_result.retcode != self.api.TRADE_RETCODE_DONE:
            # Order not filled
            raise ValueError(order_result.comment)
        else:
            if action == self.api.TRADE_ACTION_CLOSE_BY:
                # Order type "close" doesn't return a position
                return order_result
            elif action == self.api.TRADE_ACTION_SLTP:
                ticket = position
            else:
                ticket = order_result.order
            # Get position
            positions = self.api.positions_get(ticket=ticket)
            if not positions:
                time.sleep(0.1)
                positions = self.api.positions_get(ticket=ticket)
                if not positions:
                    print(f"Position {ticket} could not be returned.")
            # Position found
            if positions:
                position = positions[0]
                return position

    def market_order(self, instrument, order_size, sl=None, tp=None, magic=0, comment=""):
        order_type = self.api.ORDER_TYPE_BUY if order_size > 0 else self.api.ORDER_TYPE_SELL
        return self._order_send(
            action=self.api.TRADE_ACTION_DEAL,
            symbol=instrument,
            volume=abs(order_size),
            type=order_type,
            sl=sl,
            tp=tp,
            type_filling=self.api.ORDER_FILLING_FOK,
            magic=magic,
            comment=comment
        )

    def change_position_sltp(self, position, sl=None, tp=None, magic=0, comment=""):
        return self._order_send(
            action=self.api.TRADE_ACTION_SLTP,
            position=position.ticket,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment
        )

    def close_position(self, position, volume=None, magic=0, comment=""):
        reverse_type = self.api.ORDER_TYPE_SELL \
            if position.type == self.api.ORDER_TYPE_BUY \
            else self.api.ORDER_TYPE_BUY

        # Create an opposite market order for the specified volume
        reverse_position = self._order_send(
            action=self.api.TRADE_ACTION_DEAL,
            symbol=position.symbol,
            volume=volume or position.volume,
            type=reverse_type,
            magic=magic,
            comment=comment or "Close position"
        )

        # Close the position using the created order
        return self._order_send(
            action=self.api.TRADE_ACTION_CLOSE_BY,
            position=position.ticket,
            position_by=reverse_position.ticket,
        )

    def close_all_positions(self, instrument=None, group="*"):
        if instrument:
            positions = self.api.positions_get(symbol=instrument)
        else:
            positions = self.api.positions_get(group=group)
        return [self.close_position(position) for position in positions]

    def get_positions(self, as_dataframe=False):
        positions = self.api.positions_get()
        if as_dataframe:
            df = pd.DataFrame([position._asdict() for position in positions])
            df["datetime"] = pd.to_datetime(df["time_msc"], unit="ms")
            df.set_index("datetime", inplace=True)
            return df
        else:
            return positions

    def get_trades(self, as_dataframe=False):
        t1 = datetime(2020, 1, 1)
        t2 = datetime.utcnow() + timedelta(days=1)
        trades = self.api.history_deals_get(t1, t2)
        if as_dataframe:
            df = pd.DataFrame([trade._asdict() for trade in trades])
            df["datetime"] = pd.to_datetime(df["time_msc"], unit="ms")
            df.set_index("datetime", inplace=True)
            return df
        else:
            return trades


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
            #'1M': 'M'  # tpqoa error
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

import os
import asyncio
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

import os
os.chdir("../trader")
from trader.trader import Trader
from trader.risk_management import RiskManagement
from trader.strategies import continuation_strat

trader = Trader()
trader.add_broker('mt5')
# trader.risk_management = RiskManagement()
#
# trader.add_data("EURUSD", start="2024-12-22T22:00", granularities="tick")
# trader.add_indicator('dc', sigma=0.001, high_colname='bid', low_colname='bid')
# trader.add_strategy(continuation_strat.Strategy("EURUSD"))

trader.close_all_positions()

# trader.backtest()

#
# mt5.initialize()
# login = os.environ["FTMO_DEMO_LOGIN"]
# password = os.environ["FTMO_DEMO_PASSWORD"]
# server = os.environ["FTMO_DEMO_SERVER"]
# mt5.login(login=login, password=password, server=server)
#
# symbol = "BTCUSD"
# gmt_plus_2 = timezone(timedelta(hours=2))
#
# start_time = datetime.now(tz=gmt_plus_2) - timedelta(hours=1)
# ticks = mt5.copy_ticks_from(symbol, start_time, -1, mt5.COPY_TICKS_ALL)
# df = pd.DataFrame(ticks)
# df['datetime'] = pd.to_datetime(df['time_msc'], unit='ms', utc=True).dt.tz_convert(gmt_plus_2)
# df.set_index('datetime', inplace=True)
#
#
# def fetch_ticks(symbol, start_time):
#     ticks = mt5.copy_ticks_from(symbol, start_time, -1, mt5.COPY_TICKS_ALL)
#     if ticks is None:
#         return pd.DataFrame()  # Return an empty DataFrame if no data
#     df = pd.DataFrame(ticks)
#     df['datetime'] = pd.to_datetime(df['time_msc'], unit='ms', utc=True).dt.tz_convert(gmt_plus_2)
#     df.set_index('datetime', inplace=True)
#     return df
#
#
# # Asynchronous function to fetch data periodically
# async def load_ticks_async(symbol, interval=1):
#     print("Starting tick data fetch...")
#     start_time = datetime.now(tz=gmt_plus_2) - timedelta(minutes=5)  # Start time for initial data
#     ticks_df = pd.DataFrame()
#     while True:
#         try:
#             # Fetch new ticks
#             new_ticks = fetch_ticks(symbol, start_time)
#             if not new_ticks.empty:
#                 ticks_df = pd.concat([ticks_df, new_ticks]).drop_duplicates()
#                 start_time = new_ticks.index[-1]  # Update start_time to fetch only new data
#                 print(f"Fetched {len(new_ticks)} new ticks. Total ticks: {len(ticks_df)}")
#             # Simulate real-time by sleeping asynchronously
#             await asyncio.sleep(interval)
#         except Exception as e:
#             print(f"Error fetching ticks: {e}")
#             await asyncio.sleep(interval)  # Continue after an error
#
#
# # Main entry point for the script
# async def main():
#     await load_ticks_async(symbol)
#

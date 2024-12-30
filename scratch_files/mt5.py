import MetaTrader5 as mt5
import os
from datetime import datetime
import pandas as pd
import time
import matplotlib.pyplot as plt


mt5.initialize()

login = os.environ["FTMO_DEMO_LOGIN"]
password = os.environ["FTMO_DEMO_PASSWORD"]
server = os.environ["FTMO_DEMO_SERVER"]

mt5.login(login=login, password=password, server=server)

# df_sym = pd.DataFrame([sym._asdict() for sym in mt.symbols_get()])
# df_hist = pd.DataFrame(mt.copy_rates_range("EURUSD", mt.TIMEFRAME_H1, datetime(2024, 12, 1), datetime.now()))
# df_tick = pd.DataFrame(mt.copy_ticks_range("EURUSD", datetime(2024, 12, 3), datetime.now(), mt.COPY_TICKS_ALL))
# df_tick['datetime'] = pd.to_datetime(df_tick['time_msc'], unit='ms')
# df_tick.set_index('datetime')

symbol = "EURUSD"

# Track the last tick time to avoid duplicate ticks
last_tick_time = None

# Define the starting timestamp
start_time = datetime(2024, 12, 4, 12)  # Replace with your desired starting date and time

# Initialize an empty DataFrame to store tick data
df_tick = pd.DataFrame()

# Set up the plot
plt.ion()
fig, ax = plt.subplots()
line_bid, = ax.plot([], [], label='Bid Price', color='blue')
line_ask, = ax.plot([], [], label='Ask Price', color='red')
ax.set_xlabel('Time')
ax.set_ylabel('Price')
ax.legend()
plt.show()

while True:
    # Request tick data
    ticks = mt.copy_ticks_from(symbol, start_time, -1, mt.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        print(f"Failed to get tick data for symbol {symbol}, error code:", mt.last_error())
    else:
        # Convert ticks to DataFrame and append to existing DataFrame
        df_new = pd.DataFrame(ticks)
        # Mark the first line of df_new by setting its 'volume' column value to 1
        print(last_tick_time)

        if not df_new.empty:
            df_new['datetime'] = pd.to_datetime(df_new['time_msc'], unit='ms')
            df_new.set_index('datetime', inplace=True)

            # Merge the new data into the existing DataFrame to ensure unique index
            df_tick = df_tick.combine_first(df_new)

            # Update start_time to the last processed tick time
            last_tick_time = df_new.index[-1]
            start_time = last_tick_time.to_pydatetime()

            # Update the plot
            line_bid.set_data(df_tick.index, df_tick['bid'])
            line_ask.set_data(df_tick.index, df_tick['ask'])
            ax.relim()
            ax.autoscale_view()
            plt.draw()
            plt.pause(0.01)

    # Sleep to avoid overloading the connection (streaming every 1 second)
    time.sleep(1)

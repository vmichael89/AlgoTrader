from datetime import datetime
import pandas as pd
import os
os.chdir("../trader")
from trader.app import app, tdr

trader = tdr
tdr.add_broker("mt5")


start_date = "2024-04-01"

# create 4 weeks of data
end_date = datetime.strptime(start_date, "%Y-%m-%d") + pd.DateOffset(days=6)
trader.add_data("EURUSD", start=start_date, end=end_date.strftime("%Y-%m-%d"), granularities="1H")
start_date = (end_date + pd.DateOffset(days=1)).strftime("%Y-%m-%d")

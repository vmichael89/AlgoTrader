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
trader.add_data_stream("ETHUSD", 1)
trader.add_data_stream("BTCUSD", 1)
trader.run_live()


# trader.add_strategy(continuation_strat.Strategy("EURUSD"))

# trader.risk_management = RiskManagement()
#
# trader.add_data("EURUSD", start="2024-12-22T22:00", granularities="tick")
# trader.add_indicator('dc', sigma=0.001, high_colname='bid', low_colname='bid')

# trader.close_all_positions()

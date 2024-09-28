import os
os.chdir("../trader")
from trader.trader import Trader

trader = Trader()
trader.add_data(['EUR_USD'])

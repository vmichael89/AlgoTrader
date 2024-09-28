import os
os.chdir("../trader")
from trader.app import app, tdr

tdr.add_data(["EUR_USD"])

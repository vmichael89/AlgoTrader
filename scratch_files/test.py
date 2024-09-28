import json

from backtesting import Backtest
from trendline_breakout import trendline_breakout_dataset

with open("../data/maven_pairs.json", "r") as json_file:
    instruments = json.load(json_file)
#
instrument = "X:BTCUSD"

start = '2022-01-01'
end = '2023-01-01'
granularity = ['1', 'hour']
strategy = trendline_breakout_dataset

backtest = Backtest([instrument], start, end, granularity, strategy)
backtest.run(lookback=72, tp_mult=1, sl_mult=1.5)

data = backtest.get_trades_data()["X:BTCUSD"]
data_x = data[0]
data_y = data[1]
# data = pd.concat(data.values(), axis=0, ignore_index=True)

trades = backtest.get_results()["X:BTCUSD"]

print(trades)

data_x.to_csv('../data/model_data_btcusd_x.csv')
data_y.to_csv('../data/model_data_btcusd_y.csv')
trades.to_csv('../data/model_data_btcusd_trades.csv')



# data.to_csv('../data/model_data_btcusd_.csv')
# # #
# df = pd.read_csv('../data/model_data_levels1.csv')
#
# zeroes = df['label'].tolist().count(0)
# ones = df['label'].tolist().count(1)
#
# print(ones/(ones+zeroes))
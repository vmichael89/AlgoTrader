import os
os.chdir("../trader")
from trader.trader import Trader
from trader.algos.directional_change import DirectionalChange
# from trader.strategies import continuation_strat

trader = Trader()
trader.add_broker('mt5')
# trader.add_data_stream("ETHUSD", 1)
trader.add_indicator("ETHUSD", DirectionalChange, params=dict(sigma=0.001, high_colname='bid', low_colname='bid'))
# trader.add_strategy(continuation_strat.Strategy("ETHUSD"))
# trader.run_live()
trader.add_data("EURUSD", "2025-01-02", granularities="tick")
dc = DirectionalChange("", 0.0008, "bid", "bid")
dc.get_extremes(trader.data[0].df.tz_localize(None))
trader.data[0].df.tz_localize(None).bid.plot()
dc.extremes.extreme.plot()
print(dc.extremes)
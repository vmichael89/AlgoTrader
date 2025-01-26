import os
os.chdir("..")
import backtrader as bt
from trader.trader import Trader
os.chdir("trader")


class TestIndicator(bt.Indicator):
    # should produce a random value every 5th step
    lines = ('random_val',)
    params = (
        ('period', 5),
    )

    def __init__(self):
        self.addminperiod(self.p.period)
        self.count = 0

    def next(self):
        if self.data.datetime.datetime().minute % self.p.period == 0:
            self.count += 1
            self.l.random_val[0] = self.count

# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.data.datetime.datetime()
        print(dt.isoformat(), txt)

    def __init__(self):
        self.dc = TestIndicator()
        self.dc1 = self.dc.random_val()

    def next(self):
        self.log(f'Close, {self.data.close[0]}')
        print(self.dc1[0])

PIP = 0.0001

class RapidFire(bt.Strategy):
    def __init__(self):
        self.sma = bt.indicators.MovingAverageSimple(period=60)
        self.sar = bt.indicators.ParabolicSAR(af=0.02, afmax=0.2)
        # close above sma and sar switches from above to below
        # self.cross = bt.indicators.CrossUp(self.data.close, self.sma)
        self.cross = type('SMAcross', (bt.indicators.CrossUp,), {})(self.data.close, self.sma)
        # self.cross2 = bt.indicators.CrossUp(self.sar, self.data.close)
        self.cross2 = type('SARCross', (bt.indicators.CrossUp,), {})(self.sar, self.data.close)
        # buy signal when cross2 happened after cross, define inline class inherited from CrossUp
        # self.buy_sig = bt.indicators.CrossUp(self.cross2, self.cross)
        self.buy_sig = type('NewBuySig', (bt.indicators.CrossUp,), {})(self.cross2, self.cross)
        self.buy_sig = bt.And(self.buy_sig, self.data.close > self.sma)

    def next(self):
        if self.buy_sig:
            self.buy_bracket(
                size= 5000,
                limitprice=self.data.close[0] + 10*PIP ,
                stopprice=self.data.close[0] - 15*PIP)


if __name__ == '__main__':
    trader = Trader()
    trader.add_broker('oanda')
    trader.add_data('EUR_USD', start='2024-08-08', end='2025-01-24', granularities='1min')
    df = trader.data[0].df

    cerebro = bt.Cerebro()
    cerebro.addstrategy(RapidFire)
    cerebro.adddata(bt.feeds.PandasData(dataname=df))
    cerebro.addobserver(bt.observers.BuySell, barplot=True, bardist=0.0005)
    cerebro.run()
    cerebro.plot(style='candle')

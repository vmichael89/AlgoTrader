import pandas as pd
import numpy as np
from broker import PolygonAPI

class Backtest:
    def __init__(self, instruments, start, end, granularity, strategy, timezone="new york"):
        self.api = PolygonAPI()
        self.instruments = instruments
        self.start = start
        self.end = end
        self.granularity = granularity
        self.timezone = timezone
        self.data = self.api.get_data(instruments, start, end, granularity, timezone)
        self.strategy = strategy
        self.results = {}
        self.trades_data = {}

    def run(self, *strategy_args, **strategy_kwargs):
        for instrument in self.instruments:
            df = self.data[instrument]
            trades_and_data = self.strategy(df, *strategy_args, **strategy_kwargs)
            self.results[instrument] = self.evaluate(trades_and_data[0])
            self.trades_data[instrument] = trades_and_data[1]

    def evaluate(self, trades):
        """
        Evaluate trades and calculate performance metrics like total profit/loss, win rate, Sharpe ratio, etc.
        `trades` should be a DataFrame with trade entry/exit points and profits/losses.
        """

        total_profit = trades['return'].sum()
        num_trades = len(trades)
        win_rate = len(trades[trades['return'] > 0]) / num_trades if num_trades > 0 else 0

        # Calculate Sharpe ratio
        sharpe_ratio = np.mean(trades['return']) / np.std(trades['return']) if np.std(trades['return']) != 0 else 0

        return {
            'total_profit': total_profit,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': num_trades
        }

    def get_results(self):
        return self.results

    def get_trades_data(self):
        return self.trades_data
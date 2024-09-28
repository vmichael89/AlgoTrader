import numpy as np


class MonteCarloSimulator:
    def __init__(self, initial_balance=100, risk_percent_per_trade=1, win_rate=0.5, rr_ratio=1.0,
                 upper_threshold_pct=20, lower_threshold_pct=-20, num_simulations=1000):
        self.initial_balance = initial_balance
        self.risk_percent_per_trade = risk_percent_per_trade / 100  # Convert percentage to decimal
        self.win_rate = win_rate
        self.rr_ratio = rr_ratio
        self.upper_threshold_pct = upper_threshold_pct
        self.lower_threshold_pct = lower_threshold_pct
        self.num_simulations = num_simulations

    def simulate_trade(self, balance):
        risk_amount = balance * self.risk_percent_per_trade

        if np.random.rand() < self.win_rate:
            # Win: increase balance
            return balance + risk_amount * self.rr_ratio
        else:
            # Loss: decrease balance
            return balance - risk_amount

    def run_simulation(self):
        final_balances = []
        num_trades_list = []
        hit_upper_threshold = 0
        hit_lower_threshold = 0

        for _ in range(self.num_simulations):
            balance = self.initial_balance
            num_trades = 0

            while True:
                balance = self.simulate_trade(balance)
                num_trades += 1

                # Check if balance has reached either threshold
                if balance >= self.initial_balance * (1 + self.upper_threshold_pct / 100):
                    final_balances.append(balance)
                    num_trades_list.append(num_trades)
                    hit_upper_threshold += 1
                    break
                elif balance <= self.initial_balance * (1 + self.lower_threshold_pct / 100):
                    final_balances.append(balance)
                    num_trades_list.append(num_trades)
                    hit_lower_threshold += 1
                    break

        # Calculate percentages
        hit_upper_pct = (hit_upper_threshold / self.num_simulations) * 100
        hit_lower_pct = (hit_lower_threshold / self.num_simulations) * 100

        return num_trades_list, hit_upper_pct, hit_lower_pct

    def get_summary(self):
        num_trades_list, hit_upper_pct, hit_lower_pct = self.run_simulation()
        mean_trades = np.mean(num_trades_list)
        median_trades = np.median(num_trades_list)
        std_deviation = np.std(num_trades_list)
        return mean_trades, median_trades, std_deviation, hit_upper_pct, hit_lower_pct


if __name__ == "__main__":
    # Parameters
    initial_balance = 100
    risk_percent_per_trade = 2 # Risk 1% of the current balance per trade
    win_rate = 0.6
    rr_ratio = 1.0
    upper_threshold_pct = 10  # 20% above initial balance
    lower_threshold_pct = -10  # 20% below initial balance
    num_simulations = 1000

    # Initialize and run the simulator
    simulator = MonteCarloSimulator(
        initial_balance=initial_balance,
        risk_percent_per_trade=risk_percent_per_trade,
        win_rate=win_rate,
        rr_ratio=rr_ratio,
        upper_threshold_pct=upper_threshold_pct,
        lower_threshold_pct=lower_threshold_pct,
        num_simulations=num_simulations
    )

    # Get summary statistics
    mean_trades, median_trades, std_deviation, hit_upper_pct, hit_lower_pct = simulator.get_summary()
    print(f"Mean Number of Trades: {mean_trades:.2f}")
    print(f"Median Number of Trades: {median_trades:.2f}")
    print(f"Standard Deviation: {std_deviation:.2f}")
    print(f"Percentage of Times Hitting Upper Threshold: {hit_upper_pct:.2f}%")
    print(f"Percentage of Times Hitting Lower Threshold: {hit_lower_pct:.2f}%")

from dataclasses import dataclass


@dataclass
class RiskManagement:
    leverage = 100
    balance: float = 10000
    risk_percent_day: float = 4
    risk_total_day: float = balance * risk_percent_day / 100
    max_losses_day: int = 20
    risk_percent_trade: float = risk_percent_day / max_losses_day
    risk_total_trade: float = risk_total_day / max_losses_day

    def calc_order_size(self, price, sl):
        return self.risk_total_trade / (price - sl)


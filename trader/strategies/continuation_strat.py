from . import Strategy
from . import CriteriaManager, Low


class ContinuationStrategy(Strategy):
	def __init__(self, instrument, frequency=1):
		super().__init__(instrument, frequency)
		self.name = "Continuation Trade Strategy"

		# Trade parameters
		self.last_high = None
		self.last_low = None
		self.entry_price = None
		self.sl = None
		self.tp = None

		# Criteria to entry a trade
		self.criteria_manger = CriteriaManager([
			Low(instrument, dc_sigma=0.00003)
			# criteria.LowerHigh(max_retracement=0.5),  # restriction must be passed to next criteria
			# criteria.BreakOfRecentLow(by=0.05, update_highs_and_lows=True),
		])

		# Criteria to manage the trade: trade parameters and exit signals
		self.trade_manager = CriteriaManager([
			# Exit criteria are to be defined here
		])

	def on_new_data(self, timestamp, data):
		if self.criteria_manger.check(timestamp):
			print("Criteria met!")
			self.trader.stop_live()

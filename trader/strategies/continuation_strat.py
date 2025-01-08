from .base import Strategy
from .criteria import CriteriaManager, Extreme, BreakOfRecentExtreme


class ContinuationStrategy(Strategy):
	def __init__(self, instrument, frequency=1, sigma=0.0001, max_retracement=0.5, allow_new_extremes=True):
		super().__init__(instrument, frequency)
		self.name = "Continuation Trade Strategy"
		self.sigma = sigma
		self.max_retracement = max_retracement
		self.allow_new_extremes = allow_new_extremes

		# Criteria to entry a trade
		self.criteria_manger = CriteriaManager([
			Extreme(instrument, 'bottom', dc_sigma=sigma, max_retracement=max_retracement),
			BreakOfRecentExtreme(instrument, 'top', dc_sigma=sigma, by=0, allow_new_extremes=allow_new_extremes, max_retracement=max_retracement),
		])

		# Criteria to manage the trade: trade parameters and exit signals
		self.trade_manager = CriteriaManager([
			# Exit criteria are to be defined here
		])

	def on_new_data(self, timestamp, data):
		if self.criteria_manger.check(timestamp, data):
			print("Criteria met at ", timestamp)

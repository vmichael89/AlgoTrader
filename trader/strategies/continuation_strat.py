from . import criteria
from ..algos import directional_change


class Strategy:
	def __init__(self, instrument):
		self.trader = None
		self.instrument = instrument
		self.frequency = None
		self.name = "Continuation Trade Strategy"

		self.data = []

		# Trade parameters
		self.last_high = None
		self.last_low = None
		self.entry_price = None
		self.sl = None
		self.tp = None

		# Criteria to entry a trade
		self.criteria_manger = criteria.CriteriaManager([
			criteria.LowerHigh(max_retracement=0.5),  # restriction must be passed to next criteria
			criteria.BreakOfRecentLow(by=0.05, update_highs_and_lows=True),
		])

		# Criteria to manage the trade: trade parameters and exit signals
		self.trade_manager = criteria.CriteriaManager([
			# Exit criteria are to be defined here
		])
	
	def on_new_data(self, data):
		if self.criteria_manger.check():
			self.trader.open_trade(self.trade_manager)

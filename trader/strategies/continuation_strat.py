from . import criteria
from ..indicators import Indicator


class Strategy:
	def __init__(self, instrument, frequency=1):
		self.trader = None
		self.instrument = instrument
		self.frequency = frequency
		self.name = "Continuation Trade Strategy"

		self.data_streams = [(instrument, frequency)]

		# Trade parameters
		self.last_high = None
		self.last_low = None
		self.entry_price = None
		self.sl = None
		self.tp = None

		# Criteria to entry a trade
		self.criteria_manger = criteria.CriteriaManager([
			criteria.Low(instrument, dc_sigma=0.0005)
			# criteria.LowerHigh(max_retracement=0.5),  # restriction must be passed to next criteria
			# criteria.BreakOfRecentLow(by=0.05, update_highs_and_lows=True),
		])

		# Criteria to manage the trade: trade parameters and exit signals
		self.trade_manager = criteria.CriteriaManager([
			# Exit criteria are to be defined here
		])

	def on_add_to_trader(self, trader):
		self.trader = trader
		for criterion in self.criteria_manger.criteria:
			for attr_name in vars(criterion):
				attr = getattr(criterion, attr_name)
				if isinstance(attr, Indicator):
					# CRITERION --> TRADER (add indicator to trader if not already added)
					unique_indicator = self.trader.add_indicator(attr)
					# TRADER --> CRITERION (reassign the indicator to the criterion)
					setattr(criterion, attr_name, unique_indicator)

	def on_new_data(self, data):
		if self.criteria_manger.check():
			self.trader.open_trade(self.trade_manager)

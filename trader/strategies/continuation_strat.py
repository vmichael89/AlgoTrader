
# Setup
# - After reversal
# - Wait for 1 new higher low
# - Enough space til predicted resistance
#
# Entry when
# - Price > last high
# - SL = reversal (bid low)
# - TP
# 	- 75% SL -> R (bid)
# 	- Open
#
# Trade management
# - If new higher low
# 	- SL = last low
# 	- If bigger move
# 		- SL = break even when entry is at 50% retracement
# 		- Adjust with every candle
#
# Exit
# 	1. TP
# 	2. SL
# 	3. Sign of reversal near resistance

# add strategy with trader instance
# - currency pair

from . import criteria


class Strategy:
	def __init__(self, instrument):
		self.trader = None
		self.instrument = instrument
		self.frequency = None
		self.name = "Continuation Trade Strategy"

		self.data = None

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

		])
	
	def on_new_data(self, data):
		pass

	def step(self):
		if self.criteria_manger.check():
			self.trader.open_trade(self.trade_manager)

	def backtest(self):
		self.data = self.trader.get_data(self.instrument)

	def run_live(self):
		pass

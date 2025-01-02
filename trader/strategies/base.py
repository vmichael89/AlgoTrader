from ..indicators import Indicator


class Strategy:
    def __init__(self, instrument, frequency=1):
        self.trader = None
        self.instrument = instrument
        self.frequency = frequency
        self.name = "Strategy"
        self.data_streams = [(instrument, frequency)]
        self.criteria_manger = None
        self.trade_manager = None

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

    def on_new_data(self, timestamp, data):
        if self.criteria_manger.check():
            print("Criteria met!")
            self.trader.open_trade(self.trade_manager)

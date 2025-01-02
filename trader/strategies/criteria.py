from dataclasses import dataclass
from abc import abstractmethod
from ..indicators.directional_change import DirectionalChange


class CriteriaManager:
    def __init__(self, criteria):
        self.criteria = criteria
        self.met_criteria = [False for _ in criteria]

    def check(self, timestamp):
        for idx, criterion in enumerate(self.criteria):
            if not criterion.is_met:
                # First criterion that is not met
                if not criterion.check(timestamp):
                    return False
                else:
                    # Criterion met first time, opportunity for notification
                    self.met_criteria[idx] = True

        # All criteria met
        return True


@dataclass
class Criterion:
    is_met: bool = False

    @abstractmethod
    def check(self, timestamp):
        return False


class Low(Criterion):

    def __init__(self, instrument, dc_sigma=0.001):
        self.dc_indicator = DirectionalChange(instrument, dc_sigma, 'bid', 'bid')
        super().__init__()

    def check(self, timestamp):
        # Check if the latest extreme is a low
        extremes = self.dc_indicator.extremes
        if not extremes.empty:
            latest_extreme = extremes.iloc[-1]
            if latest_extreme['type'] == 'bottom':
                if latest_extreme['conf_time'] == timestamp:
                    print("Extreme: ", extremes.to_string())
                    self.is_met = True
        return self.is_met

#
# @dataclass
# class High(Criterion):
#     def check(self):
#         pass
#
#
# @dataclass
# class LowerHigh(Criterion):
#     max_retracement: float = 0
#
#     def check(self):
#         pass
#
#
# @dataclass
# class BreakOfRecentLow(Criterion):
#     by: float = 0
#     update_highs_and_lows: bool = True
#
#     def check(self):
#         pass
#
#
# @dataclass
# class HigherLow(Criterion):
#     cm = CriteriaManager([
#         Low(),
#         High(),
#         Low()
#     ])
#
#     def check(self):
#         return self.cm.check()
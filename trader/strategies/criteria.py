from dataclasses import dataclass
from abc import abstractmethod
from ..indicators.directional_change import DirectionalChange


class CriteriaChainTerminatedException(Exception):
    pass


class CriteriaManager:
    def __init__(self, criteria):
        self.criteria = criteria
        self.met_criteria = [False for _ in criteria]

    def check(self, timestamp):
        try:
            next_criterion_idx = self.met_criteria.index(False)
            self.met_criteria[next_criterion_idx] = self.criteria[next_criterion_idx].check(timestamp)
            if all(self.met_criteria):
                self._reset()
                return True
        except CriteriaChainTerminatedException:
            self._reset()
            return False

    def _reset(self):
        self.met_criteria = [False for _ in self.criteria]


class Criterion:

    @abstractmethod
    def check(self, timestamp):
        return False


class Extreme(Criterion):

    def __init__(self, extreme_type, instrument, dc_sigma, max_retracement=None):
        self.extreme_type = extreme_type
        self.max_retracement = max_retracement
        self.dc_indicator = DirectionalChange(instrument, dc_sigma, 'bid', 'bid')
        super().__init__()

    def check(self, timestamp):
        extremes = self.dc_indicator.extremes
        if not extremes.empty:
            latest_extreme = extremes.iloc[-1]

            is_new_extreme = latest_extreme['conf_time'] == timestamp
            type_valid = latest_extreme['type'] == self.extreme_type
            retracement_valid = (
                    self.max_retracement is None or
                    (latest_extreme['retracement'] < self.max_retracement)
            )

            if is_new_extreme and type_valid:

                if retracement_valid:
                    print("Extreme: ", extremes.to_string())
                    return True
                else:
                    raise CriteriaChainTerminatedException

        return False

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
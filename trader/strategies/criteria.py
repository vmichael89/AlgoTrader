from dataclasses import dataclass
from abc import abstractmethod
from ..indicators.directional_change import DirectionalChange


class CriteriaManager:
    def __init__(self, criteria):
        self.criteria = criteria
        self.met_criteria = [False for _ in criteria]

    def check(self):
        for idx, criterion in enumerate(self.criteria):
            if not criterion.is_met:
                # First criterion that is not met
                if not criterion.check():
                    return False
                else:
                    # Criterion met first time, opportunity for notificatoin
                    self.met_criteria[idx] = True

        # All criteria met
        return True


@dataclass
class Criterion:
    is_met: bool = False

    def __post_init__(self):
        pass

    @abstractmethod
    def check(self):
        return False


class Low(Criterion):

    def __init__(self, instrument, dc_sigma=0.0005):
        self.dc_indicator = DirectionalChange(instrument, dc_sigma)
        super().__init__()

    def check(self):
        # Check if the latest extreme is a low
        extremes = self.dc_indicator.extremes
        if not extremes.empty and extremes.iloc[-1]['type'] == 'bottom':
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
from dataclasses import dataclass
from abc import abstractmethod


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

    @abstractmethod
    def check(self):
        return False


@dataclass
class LowerHigh(Criterion):
    max_retracement: float = 0

    def check(self):
        pass


@dataclass
class BreakOfRecentLow(Criterion):
    by: float = 0
    update_highs_and_lows: bool = True

    def check(self):
        pass

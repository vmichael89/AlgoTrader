from abc import abstractmethod
from ..indicators.directional_change import DirectionalChange


class CriteriaChainTerminatedException(Exception):
    pass


class CriteriaManager:
    def __init__(self, criteria):
        self.criteria = criteria
        self.met_criteria = [[False for _ in criteria]]

    def check(self, timestamp, data):
        try:
            next_criterion_idx = self.met_criteria[-1].index(False)
            if self.criteria[next_criterion_idx].check(timestamp, data):
                self.met_criteria[-1][next_criterion_idx] = timestamp
            if all(self.met_criteria[-1]):
                self._reset()
                return True
        except CriteriaChainTerminatedException:
            self._reset()
            return False

    def _reset(self):
        self.met_criteria.append([False for _ in self.criteria])


class Criterion:

    @abstractmethod
    def check(self, timestamp, data):
        return False


class Extreme(Criterion):

    def __init__(self, instrument, extreme_type, dc_sigma, max_retracement=None):
        self.extreme_type = extreme_type
        self.max_retracement = max_retracement
        self.dc_indicator = DirectionalChange(instrument, dc_sigma, 'bid', 'bid')
        super().__init__()

    def check(self, timestamp, data):
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
                    return True
                else:
                    raise CriteriaChainTerminatedException

        return False


class BreakOfRecentExtreme(Criterion):
    def __init__(self, instrument, extreme_type, dc_sigma, by, update_highs_and_lows):
        self.extreme_type = extreme_type
        self.by = by
        self.update_highs_and_lows = update_highs_and_lows
        self.dc_indicator = DirectionalChange(instrument, dc_sigma, 'bid', 'bid')

        self.recent_extreme = None
        self.threshold = None
        super().__init__()

    def check(self, timestamp, data):
        extremes = self.dc_indicator.extremes
        # Get latest extreme of the right type and calculate the threshold
        if not self.threshold:
            self.recent_extreme = extremes[extremes['type'] == self.extreme_type].iloc[-1]
            self.threshold = self.recent_extreme['extreme'] * (1 + self.by)

        if self.update_highs_and_lows:
            # Check if recent_extreme has changed
            new_recent_extreme = extremes[extremes['type'] == self.extreme_type].iloc[-1]
            if new_recent_extreme.name != self.recent_extreme.name:
                self.recent_extreme = new_recent_extreme
                self.threshold = self.recent_extreme['extreme'] * (1 + self.by)

        # Check if the threshold has been crossed
        if data['bid'] > self.threshold:
            return True

        return False
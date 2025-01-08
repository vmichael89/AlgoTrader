from abc import abstractmethod

import pandas as pd
import plotly.graph_objects as go

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
        for criterion in self.criteria:
            criterion.reset()


class Criterion:
    def __init__(self):
        self._initial_state = self.__dict__.copy()  # Save initial state
        self.plot_object_list = []

    @abstractmethod
    def check(self, timestamp, data):
        return False

    def reset(self):
        # Restore the initial state
        for key, val in self._initial_state.items():
            setattr(self, key, val)

    def plot_objects(self):
        """Returns a list of plotly graph objects"""
        return []


class Extreme(Criterion):

    def __init__(self, instrument, extreme_type, dc_sigma, max_retracement=None):
        self.extreme_type = extreme_type
        self.max_retracement = max_retracement
        self.dc_indicator = DirectionalChange(instrument, dc_sigma, 'bid', 'bid')

        self.extreme = None
        self.prev_extreme = None
        super().__init__()

    def reset(self):
        self.extreme = None
        self.prev_extreme = None

    def check(self, timestamp, data):
        extremes = self.dc_indicator.extremes
        if not extremes.empty:
            self.extreme = extremes.iloc[-1]
            self.prev_extreme = extremes.iloc[-2] if len(extremes) > 1 else None

            is_new_extreme = self.extreme['conf_time'] == timestamp
            type_valid = self.extreme['type'] == self.extreme_type
            retracement_valid = (
                    self.max_retracement is None or
                    (self.extreme['retracement'] < self.max_retracement)
            )

            if is_new_extreme and type_valid:
                if retracement_valid:
                    self.plot_object_list.extend(self.plot_objects())
                    return True
                else:
                    self.plot_object_list.extend(self.plot_objects())
                    raise CriteriaChainTerminatedException

        return False

    def plot_objects(self):
        # Plot horizontal retracement level from the previous extreme to the current one
        if self.prev_extreme is not None:
            retracement_level = self.prev_extreme['extreme'] - self.prev_extreme['total_price_movement'] * self.max_retracement
            return [
                go.Scatter(
                    x=[self.prev_extreme.name, self.extreme.name],
                    y=[retracement_level, retracement_level],
                    mode='lines',
                    line=dict(color='black', width=1),
                    name='Retracement'
                )
            ]
        return []


class BreakOfRecentExtreme(Criterion):
    def __init__(self, instrument, extreme_type, dc_sigma, by=0, max_retracement=None, allow_new_extremes=False):
        self.extreme_type = extreme_type
        self.by = by
        self.allow_new_extremes = allow_new_extremes
        self.max_retracement = max_retracement
        self.dc_indicator = DirectionalChange(instrument, dc_sigma, 'bid', 'bid')

        self.timestamp = None
        self.recent_extreme = None
        self.break_threshold = None
        self.max_retracement_threshold = None
        self.df = pd.DataFrame()
        self.cnt = 0
        super().__init__()

    def reset(self):
        self.recent_extreme = None
        self.break_threshold = None
        self.max_retracement_threshold = None

    def check(self, timestamp, data):
        self.timestamp = timestamp
        # Get latest extreme of the right type, but only once if allow_new_extremes is False
        try:
            self.recent_extreme = self.dc_indicator.extremes.query(f'type == "{self.extreme_type}"').iloc[-1] \
                if (self.allow_new_extremes or self.recent_extreme is None) \
                else self.recent_extreme
        except IndexError:
            # No extremes of the right type yet
            return False
        # Note: Now, there should be at least one extreme of the right type

        # Update the break threshold
        self.break_threshold = self.recent_extreme['extreme'] * (1 + self.by)

        # Set the max retracement threshold ONCE
        if self.max_retracement and self.max_retracement_threshold is None:
            self.max_retracement_threshold = self.recent_extreme['extreme'] - self.max_retracement * self.recent_extreme['total_price_movement']

        # Save the data
        self.df = pd.concat([self.df, pd.DataFrame(
            data={
                'recent_extreme': self.recent_extreme['extreme'],
                'break_threshold': self.break_threshold,
                'max_retracement_threshold': self.max_retracement_threshold,
                'count': self.cnt},
            index=[timestamp])])

        # Correct the sign of the comparison
        sign = 1 if self.extreme_type == 'top' else -1

        # Check if the break threshold has been crossed
        if sign * (data['bid'] - self.break_threshold) > 0:
            return True

        # Check if the max retracement has been violated
        if self.max_retracement_threshold:
            if sign * (data['bid']- self.max_retracement_threshold) < 0:
                raise CriteriaChainTerminatedException

        return False

    def plot_objects(self):
        # Return a scatter for break threshold and max retracement threshold
        return [
            go.Scatter(
                x=self.df.index,
                y=self.df['break_threshold'],
                mode='markers',
                line=dict(color='black', width=1),
                name='Break threshold'
            ),
            go.Scatter(
                x=self.df.index,
                y=self.df['max_retracement_threshold'],
                mode='markers',
                line=dict(color='red', width=1),
                name='Max retracement threshold'
            )
        ]

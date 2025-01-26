import math
import backtrader as bt

class DirectionalChange(bt.Indicator):
    lines = ('extreme', 'overshoot')
    params = (
        ('sigma', 0.0001),
        ('high_colname', 'high'),
        ('low_colname', 'low'),
    )

    def __init__(self):
        # TODO: add timezone support
        # TODO: specify the data source
        self.high = getattr(self.data, self.p.high_colname)
        self.low = getattr(self.data, self.p.low_colname)
        self.last_overshoot = self.l.overshoot()

        self.up_zig = False
        self.down_zig = False
        self.initial_timestamp = None
        self.initial_high = None
        self.initial_low = None
        self.timestamp = None

    def _get_last_overshoot(self):
        for val in self.l.overshoot.array[::-1]:
            if not math.isnan(val):
                return val
        return None

    def next(self):
        if not self.initial_high or not self.initial_low:
            self.initial_high = self.high[0]
            self.initial_low = self.low[0]

        # trend initialization / wait for first overshoot event
        if not (self.up_zig or self.down_zig):

            if self.low <= self.initial_high - self.p.sigma:
                # save time/val from current overshoot event
                self.down_zig = True
                self.l.overshoot[0] = self.low[0]

            elif self.high >= self.initial_low + self.p.sigma:
                # save time/val from current overshoot event
                self.up_zig = True
                self.l.overshoot[0] = self.high[0]

        elif self.up_zig:
            if overshoot_event := self.high[0] > self.l.overshoot[-1]:
                self.l.overshoot[0] = self.high[0]

            elif self.low <= self.l.overshoot[-1] - self.p.sigma:
                self.down_zig = True
                self.up_zig = False
                self.l.extreme[0] = self.l.overshoot[-1]
                self.l.overshoot[0] = self.low[0]

            else:
                self.l.overshoot[0] = self.l.overshoot[-1]

        elif self.down_zig:
            if undershoot_event := self.low[0] < self.l.overshoot[-1]:
                self.l.overshoot[0] = self.low[0]
            elif self.high >= self.l.overshoot[-1] + self.p.sigma:
                self.up_zig = True
                self.down_zig = False
                self.l.extreme[0] = self.l.overshoot[-1]
                self.l.overshoot[0] = self.high[0]

            else:
                self.l.overshoot[0] = self.l.overshoot[-1]

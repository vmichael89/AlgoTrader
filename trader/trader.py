import os
import datetime

from .broker import OandaBroker
from .data import Data


class Trader:

    def __init__(self):
        self.broker = OandaBroker()
        self.data = []

    def add_data(self, instruments, **kwargs):
        today = datetime.datetime.utcnow().date().strftime('%Y-%m-%d')
        seven_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).date().strftime('%Y-%m-%d')

        start = kwargs.get('start', seven_days_ago)
        end = kwargs.get('end', today)
        granularity = kwargs.get('granularity', 'H1')
        price = kwargs.get('price', 'M')

        # Check if data is locally available
        for instrument in instruments:
            for p in price:
                dummy_data = Data(symbol=instrument, start=start, end=end, granularity=granularity, price=p, df=[])
                if os.path.exists(str(dummy_data) + '.pkl'):
                    print(f'Loading from file: {instrument} data from {start} to {end} with granularity {granularity} and price {p}')
                    self.data.append(dummy_data.load())
                else:
                    print(f'Fetching from broker: {instruments} data from {start} to {end} with granularity {granularity} and price {p}')
                    self.data.extend(self.broker.get_data(instrument, start, end, granularity, p))

    def remove_data(self, index):
        data = self.data.pop(index)
        print(f'Removed {data}')

    def save_data(self, save_all=False, data: Data = None, indices=None):
        """Save specific Data to file.

        .save_data(save_all=True) to save all data.
        .save_data(data=data_obj) to save only selected data.
        .save_data(indices=[0,2] to save traders 0th and 2nd data object."""

        if save_all:
            for data in self.data:
                data.save()

        elif indices:
            for i in indices:
                self.data[i].save()

        elif data:
            data.save()


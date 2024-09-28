import datetime

from .broker import OandaBroker


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

        print(f'Fetching data from {start} to {end} with granularity {granularity} and price {price}')

        self.data.extend(self.broker.get_data(instruments, start, end, granularity, price))


if __name__ == '__main__':
    trader = Trader()
    trader.add_data(['EUR_USD'])

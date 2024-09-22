import asyncio
import threading
import backtrader as bt
import datetime


class CustomLiveData(bt.feeds.DataBase):
    params = (
        ('live', True),  # Indicate it's live
        ('qcheck', 0.5),  # Check queue every 0.5 seconds
    )

    def __init__(self):
        super(CustomLiveData, self).__init__()
        self.live_data_queue = []  # Queue where live data (candles) are stored
        self.current_candle = None

    def islive(self):
        return True  # Notify Cerebro that this is a live data feed

    def _load(self):
        if not self.live_data_queue:
            return None  # No new data yet, but keep waiting in live mode

        # Pop the next candle from the live data queue
        self.current_candle = self.live_data_queue.pop(0)

        # Define OHLCV (Open, High, Low, Close, Volume)
        self.lines.datetime[0] = bt.date2num(self.current_candle['datetime'])
        self.lines.open[0] = self.current_candle['open']
        self.lines.high[0] = self.current_candle['high']
        self.lines.low[0] = self.current_candle['low']
        self.lines.close[0] = self.current_candle['close']
        self.lines.volume[0] = self.current_candle['volume']
        self.lines.openinterest[0] = 0  # Default open interest

        return True  # Data has been loaded successfully


# Async function to simulate live data feeding
async def simulate_live_data(data_feed, stop_event, interval_seconds=5):
    while not stop_event.is_set():
        # Create a mock candle
        next_candle = {
            'datetime': datetime.datetime.utcnow(),
            'open': 1.1000,
            'high': 1.1050,
            'low': 1.0950,
            'close': 1.1025,
            'volume': 100
        }

        # Add the candle to the queue
        data_feed.live_data_queue.append(next_candle)

        # Wait for the next interval
        await asyncio.sleep(interval_seconds)

    print("Live data simulation stopped.")


# Create a Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])


# Function to run the async event loop in a separate thread
def run_async_loop(data_feed, stop_event, interval_seconds):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(simulate_live_data(data_feed, stop_event, interval_seconds))


if __name__ == "__main__":
    # Create a new instance of the custom live data feed
    data = CustomLiveData()

    # Create a stop event to signal when the thread should stop
    stop_event = threading.Event()

    # Start the async live data simulation in a separate thread
    interval_seconds = 5
    live_data_thread = threading.Thread(target=run_async_loop, args=(data, stop_event, interval_seconds))
    live_data_thread.daemon = True  # Ensure the thread stops when the main program exits
    live_data_thread.start()

    # Initialize Cerebro and add the strategy
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)

    # Add the custom live data feed to Cerebro
    cerebro.adddata(data)

    try:
        # Run the backtrader engine
        cerebro.run()
    finally:
        # Signal the live data thread to stop after Cerebro finishes
        stop_event.set()  # Signal the thread to stop
        live_data_thread.join()  # Ensure the thread has finished
        print("Live data thread stopped.")

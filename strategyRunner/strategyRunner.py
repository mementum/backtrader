import threading
import backtrader as bt
from backtrader.feeds.tvLiveDatafeed import tvLiveDatafeed as tld

class strategyRunner(threading.Thread):

    def __init__(self, data_collector, strategy, symbol, exchange, interval):
        self.cerebro = bt.Cerebro()
        self.cerebro.addstrategy(strategy)
        self.cerebro.adddata(tld(data_collector, symbol, exchange, interval))
        threading.Thread.__init__(self)
    
    def run(self):
        self.cerebro.run()
        
    def stop(self):
        pass
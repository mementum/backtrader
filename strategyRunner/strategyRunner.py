'''
TODO:
'''

import threading
import backtrader as bt
from backtrader.feeds.tvLiveDatafeed import tvLiveDatafeed as tld

class strategyRunner(threading.Thread):

    def __init__(self, data_collector, sql_input, TUID, asset_id, strategy, except_hand_callback):
        # just save references which will be used when thread started - avoid raising any exception in init stage
        self.data_collector=data_collector
        self.sql_input=sql_input
        self.TUID=TUID
        self.strategy=strategy
        self.asset_id=asset_id
        self.callback_func=except_hand_callback
        threading.Thread.__init__(self)
    
    def run(self):
        try: # try executing the strategy - we might get raised exception (if user entered something wrong in strategy)
            self.live_feed=tld(self.data_collector, self.asset_id) # this feed will register for asset set (symbol, exchange, interval) specified with asset_id
            self.cerebro = bt.Cerebro()
            self.cerebro.addstrategy(self.strategy, sql_input=self.sql_input, TUID=self.TUID)
            self.cerebro.adddata(self.live_feed)
            self.cerebro.run()
        except Exception as e: # notify the caller about this strategy thread failing with exception e and close
            self.live_feed.remove_callback()
            self.callback_func(e)
        
    def stop(self):
        self.live_feed.remove_callback() # first remove callback from data_collector - then we can be sure that nothing else is calling receive_data() method
        self.live_feed.receive_data("EXIT")
        
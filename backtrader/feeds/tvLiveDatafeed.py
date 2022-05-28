import queue
from backtrader import date2num
from backtrader.feeds import DataBase

class tvLiveDatafeed(DataBase): # PARENT class is AbstractDataBase

    def __init__(self, tv_datafeed, symbol, exchange, interval):
        self.newData = False # flag to indicate if data in queue available; set by receive_data and cleared by _load only when queue is empty
        self.tdr=tv_datafeed
        self.asset_id=self.tdr.add_symbol(symbol, exchange, interval) # add symbol into set of symbols we monitor and collect data for; if already added then existing asset_id will be returned
        self.tdr.add_callback(self.asset_id, self.receive_data) # add callback method for this symbol
        self.data_queue=queue.Queue() # queue where all the new data is put for the _load() method to process
        
    def start(self):
        super().start() 

    def receive_data(self, data): # this function is called by the tvDatafeedRealtime whenever the symbol we use in this datafeed has a new value
        self.data_queue.put(data) # put new data in to queue
        self.newData=True # set the flag so _load() knows there is new data

    def _load(self):  # this is called inside the load() method in AbstractDataBase and will actually assign data to lines
        if self.newData:
            data=self.data_queue.get() # get next available data bar
            # add new data togetehr with its datetime into lines
            self.lines.datetime[0] = date2num(data.index[0])
            # Get the rest of the unpacked data
            self.lines.open[0] = data.open[0]
            self.lines.high[0] = data.high[0]
            self.lines.low[0] = data.low[0]
            self.lines.close[0] = data.close[0]
            self.lines.volume[0] = data.volume[0]
            self.lines.openinterest[0] = 0 # there is no such data in tvDatafeed so keep it zero
            
            # check if queue is now empty (last data sample for now)
            if self.data_queue.empty():
                self.newData=False
            return True
        else:
            return None

    def islive(self):
        '''Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated'''
        return True

    def stop(self):
        '''Stops and tells the store to stop'''
        super().stop() # calls PARENT class (AbstractDataBase) stop() method
        
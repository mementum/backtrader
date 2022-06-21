'''
The class defined in this module utilizes tvDatafeed module and 
extends its capability to collect multiple data samples from 
TradingView in near realtime and continuously. Instance of this 
class acts as a data source and once started with run(), it will 
produce data sample for new asset set (asset, exchange, interval) 
each time a new bar becomes available in TradingView. 
Data is provided in near realtime which means as quickly 
as possible, but there is inherent delay of couple of seconds. Users 
can add and remove new asset sets during runtime, but only one unique 
asset set is allowed and others such will be rejected (None returned). 
User can add one or multiple callback functions to each asset set. 
These callback functions will be called once new data becomes 
available for that asset set. This class implements threading so once 
run() is called user code can continue to perform other tasks. Also, 
the callback functions can include waiting or blocking statements, it 
will not affect other callback functions and their timing. However, 
care should be taken to not block indefinitely because next 
data sample will not be processed until previous call to callback 
function has returned.

'''

from tvDatafeed import TvDatafeed
from datetime import datetime as dt
from tvDatafeed.assetManager import assetManager
import threading, queue
import time

class tvDatafeedRealtime():
    '''
    Class for generating data samples near realtime from TradingView.
    
    Methods
    -------
    add_symbol(symbol, exchange, interval, timeout=-1)
        add a new asset set to monitor, the required input is identical
        to TvDatafeed.get_hist() method input, refer to that documentation
        for more info. This method can block when called after run() and
        optional timeout argument can specify a timeout for blocking.
        Method will return asset_id (int) as a reference  for that asset 
        set.
    add_callback(asset_id, callback_func, timeout=-1)
        add a new callback function for some asset set under monitor. The
        asset set is specified with asset_id parameter (returned by 
        add_symbol). Second parameter must be the callback function to
        be called. This method can block if called after run() and user
        can specify an optional timeout parameter for the operation.
    run()
        start retrieving data samples, after this the instance will 
        start checking for data updates and calling callback functions if 
        there are any
    stop()
        opposite operation to run() - shut down and stop retrieving data 
        samples
    '''
    def __init__(self, username=None, password=None, chromedriver_path=None, auto_login=True):
        '''
        Parameters
        ----------
        username : str, optional
            TradingView username (default None)
        password : str, optional
            TradingView password (default None)
        chromedriver_path : str, optional
            path to chromedriver on local machine (default None)
        auto_login : boolean, optional
            specify if system tries to login or uses public TradingView 
            interface by default (default True)
        '''
        self.__am=assetManager()
        self.__tv_datafeed = TvDatafeed(username=username, password=password, chromedriver_path=chromedriver_path, auto_login=auto_login) 
        self.__timeout_datetime = None # this specifies the time waited until next sample(s) are retrieved from tradingView 
        
        self.__callback_threads = {} # this holds reference to all the callback threads running, key values will be queue object references
        self.__main_thread = None # this variable is used for referencing the main thread running collect_data_loop
        self.__shutdown=threading.Event() # this will be used to close the collect_data_loop thread
    
    def add_symbol(self, symbol, exchange, interval, timeout=-1):
        '''
        Add a symbol on a specific exchange with specific interval into 
        monitor list. Method will return an ID which can be used to
        reference this asset set (symbol, exchange, interval) in later
        operations. Method is a blocking operation.
        
        Parameters
        ----------
        symbol : str
            ticker for the asset to retrieve data for
        exchange : str
            exchange or market from where to retrieve data
        interval : Interval
            time interval for the data bar
        timeout : int
            time to wait before timing out on operation
        '''
        self.__am.get_lock(timeout)
        asset_id=self.__am.add_asset(symbol, exchange, interval)
        if asset_id is not None: #  if this asset was not already under monitoring, no duplicates are allowed
            in_list=self.__am.get_timeframe(interval) # get the next update time for this interval
            if in_list is None: # None if we are not monitoring this interval yet
                data=self.__tv_datafeed.get_hist(symbol,exchange,n_bars=1,interval=interval) # get 1-bar data for this symbol and interval
                self.__am.add_timeframe(interval, data.index.to_pydatetime()[0]) # add this datetime into list of timeframes we monitor; to_pydatetime converts into list of datetime objects
        
        self.__am.drop_lock() 
        
        if self.__main_thread is None: # if main thread is not running then start (might have not yet started or might have closed when all asset sets were removed)
            self.__main_thread = threading.Thread(target=self.__collect_data_loop, args=(self.__shutdown,))
            self.__main_thread.start() 
        
        return asset_id
    
    def del_symbol(self, asset_id, timeout=-1):
        self.__am.get_lock(timeout)
        asset=self.__am.get_asset(asset_id)
        for queue in asset.get_callback_queues(): # remove and close all associated callback threads and their references
            self.__callback_threads.pop(queue) # remove the callback thread reference from the dictionary
            queue.put("EXIT") # send exit signal to thread
        self.__am.del_asset(asset_id) # delete the asset itself
        self.__am.drop_lock()
        
    def __collect_data(self, shutdown):
        if self.__timeout_datetime is not None:
            wait_time=self.__timeout_datetime-dt.now() # calculate the time in seconds to next timeout
            if shutdown.wait(wait_time.total_seconds()): # if we received an event during waiting then it will return True
                raise RuntimeError() # raise an exception so we'll exit the while loop and close the thread
            
        self.__am.get_lock() # we will not time out, but wait however long necessary
        updated_timeframes=self.__am.get_updated_timeframes() # returns a list of booleans for all intervals that we monitor
        self.__timeout_datetime=self.__am.get_timeout_dt() # get datetime when next sample should becomes available (wait time)
        
        for inter in updated_timeframes:
            for asset in self.__am.get_grouped_assets(inter): # go through all the assets in this interval group 
                retry_counter=0 # keep track of how many tries so we give up at some point
                while True:
                    data=self.__tv_datafeed.get_hist(asset.symbol,asset.exchange,n_bars=1,interval=asset.interval) # get the latest data bar for this asset
                    
                    # if the retrieved samples datetime does not equal the old datetime then it is new sample, otherwise try again
                    if asset.get_updated_value() != data.index.to_pydatetime()[0]:
                        asset.set_updated_value(data.index.to_pydatetime()[0]) # update the datetime of the last sample
                        break
                    elif retry_counter >= 100: # if more than 100 times we get old data then abort (50s)
                        raise ValueError("Failed to retrieve new data from TradingView")
                    
                    time.sleep(0.5)
                    
                    if shutdown.is_set(): # check if shutdown has been signaled 
                        raise RuntimeError() # raise an exception so we'll exit the while loop and close the thread
                
                # put this new data into all the queues for all the callback function threads that are expecting this data sample
                for queue in asset.get_callback_queues():
                    queue.put(data)
        
        self.__am.drop_lock() 
    
    def __callback_thread(self, callback_function, queue):
        while True:
            data=queue.get() # this blocks until we get new data sample
            if isinstance(data,str): # string means that we received "EXIT" keyword
                break # stop looping and close the thread
            
            callback_function(data) # call the function with data sample
    
    def add_callback(self, asset_id, callback_func, timeout=-1):
        '''
        Method to add a function that will be called when new data sample
        (candlebar) becomes available for the specified asset set 
        (symbol, exchange, interval). One asset set can have multiple 
        callback functions attached to it and they will be called in
        separate threads. Method is a blocking operation.
        
        Parameters
        ----------
        asset_id : int
            asset set ID which is returned by the add_symbol() method
        callback_func : function
            function to be called
        timeout : int
            time to wait before timing out on operation
        '''
        q=queue.Queue() # create a queue for this asset thread
        
        self.__am.get_lock(timeout) 
        queue_id=self.__am.add_queue(asset_id, q) # save a reference for this queue with this specific asset set (symbol exchange, interval)
        self.__am.drop_lock() 
        
        t=threading.Thread(target=self.__callback_thread, args=(callback_func,q)) # create a thread running callback_thread function      
        self.__callback_threads[q]=t  # use queue object reference to track callback threads because they are mapped 1-to-1; this way we hide thread reference from user
        t.start() # start callback function thread 
        
        return [asset_id, queue_id] # return a list containing asset_id, queue_id and reference to thread calling the callback function
    
    def del_callback(self, asset_queue_pair, timeout=-1):
        '''
    
        '''
        self.__am.get_lock(timeout)
        q=self.__am.get_queue(asset_queue_pair[0], asset_queue_pair[1]) # get the actual queue instance ref before deleting it
        self.__am.del_queue(asset_queue_pair[0], asset_queue_pair[1]) # remove this queue from that assets list so no more data is sent to that queue
        self.__am.drop_lock() 
        q.put("EXIT") # send the exit signal to that thread
        self.__callback_threads.pop(q) # remove the thread reference from the dictionary
        
    def __collect_data_loop(self, shutdown):
        try: 
            while not shutdown.is_set(): # loop this function in this thread until shutdown signal received
                self.__collect_data(shutdown)
                if self.__timeout_datetime is None: # if None after running collect_data then no asset sets added and we will stop thread because nothing to do
                    self.__main_thread = None # clear this reference because this thread will be closed
                    return 
        except RuntimeError: # this is expected if shutdown signal was sent
            if self.__am.islocked():
                self.__am.drop_lock() # release the lock so in case something is blocked because of this
            # send a close signal to all the callback threads
            for asset in self.__am.get_asset_list():
                for queue in asset.get_callback_queues():
                    queue.put("EXIT") 
        
    def __del__(self):
        # make sure that all threads are stopped
        self.__shutdown.set()
        self.__main_thread.join() # wait until all threads are closed down
    
    def stop(self):
        '''
        Stop the data collecting loop thread - this must be called before 
        deleting the object so all the threads are properly shut down. 
        '''
        if self.__main_thread is not None:
            self.__del__()  
        
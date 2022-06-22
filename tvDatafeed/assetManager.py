'''
This is a supporting module for the tvDatafeedRealtime module to 
provide assetManager and asset classes which are used to keep
track of specific assets and provide general methods to manage 
them.

TODO:

'''

from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rd
import threading

class asset(object):

    def __init__(self, symbol, exchange, interval):
        self.symbol=symbol
        self.exchange=exchange
        self.interval=interval
        
        self.updated=None # tracks last update datetime for this asset data sample
        self.callback_queues={} # dictionary containing queues for all the callback function threads for this asset set
    
    def __eq__(self, other):
        if isinstance(other, self.__class__): # make sure that they are the same class 
            if self.symbol == other.symbol and self.exchange == other.exchange and self.interval == other.interval: # these attributes need to be identical
                return True

        return False
    
    def get_updated_value(self):
        return self.updated
    
    def set_updated_value(self,dt):
        self.updated=dt
    
    def add_queue(self, queue):
        for i in range(len(self.callback_queues)+1): # keys are integer values starting from 0, loop through all keys + 1
            if i not in self.callback_queues: # if any key before the highest key has been released (deleted) then we shall use that one, otherwise we take new highest number
                self.callback_queues[i]=queue
                return i
     
    def del_queue(self, queue_id):
        return self.callback_queues.pop(queue_id, None) # remove key-value pair from dict, if not existing then None is returned otherwise the queue object itself is returned
    
    def get_queue(self,queue_id):
        return self.callback_queues[queue_id]
        
    def get_callback_queues(self):
        return self.callback_queues.values()

class assetManager(object):
    
    def __init__(self):
        self.__assets={} # dictionary which has int as keys and asset objects as values
        self.__grouped_assets={} # dictionary which has lists as values and Interval enum as keys
        self.__update_times={} # dictionary which has datetime as value and Interval enum as keys
        
        self.__lock=threading.Lock()
        
        # this array contains different time periods available in TradingView; we use them to increment to next execution time
        self.__timeframes={"1":rd(minutes=1), "3":rd(minutes=3), "5":rd(minutes=5), \
                         "15":rd(minutes=15), "30":rd(minutes=30), "45":rd(minutes=45), \
                         "1H":rd(hours=1), "2H":rd(hours=2), "3H":rd(hours=3), "4H":rd(hours=4), \
                         "1D":rd(days=1), "1W":rd(weeks=1), "1M":rd(months=1)}
    
    def add_asset(self, symbol, exchange, interval):
        new_asset=asset(symbol, exchange, interval)
        if new_asset in self.__assets.values(): # if this asset set is already among assets that we monitor 
            return list(self.__assets.keys())[list(self.__assets.values()).index(new_asset)] # then simply return the asset_id of the existing asset
        
        for i in range(len(self.__assets)+1): # keys are integer values starting from 0, loop through all keys + 1
            if i not in self.__assets: # if any key before the highest key has been released (deleted) then we shall use that one, otherwise we take new highest number
                self.__assets[i]=new_asset 
                
                # create a new interval group in grouped assets if not already existing
                if new_asset.interval.value not in self.__grouped_assets:
                    self.__grouped_assets[new_asset.interval.value]=[] 
                
                # update the grouped asset list
                for a in self.__assets.values():
                    if a not in self.__grouped_assets[a.interval.value]: # if we don't already have it listed
                        self.__grouped_assets[a.interval.value].append(a)
                                
                return i
    
    def get_asset(self, asset_id):
        return self.__assets[asset_id]
    
    def get_timeframe(self, interval):
        if interval.value in self.__update_times: # if this timeframe is in the monitor list
            return self.__update_times[interval.value] # return datetime object of the next update time for this timeframe
        
        return None # not in the list so return None
    
    def add_timeframe(self, interval, update_dt):
        if interval.value not in self.__update_times:
            self.__update_times[interval.value]=update_dt+self.__timeframes[interval.value] # add this timeframe into list of timeframes wee need to monitor and update; add interval so we get the datetimefor next time it should update
            return interval.value
        
        return None # if we already have this timeframe under monitoring 
    
    def __del_timeframe(self, interval):
        del self.__update_times[interval.value]
            
    def del_asset(self, asset_id):
        self.__grouped_assets[self.__assets[asset_id].interval.value].remove(self.__assets[asset_id])
        if not self.__grouped_assets[self.__assets[asset_id].interval.value]: # if the list is now empty
            del self.__grouped_assets[self.__assets[asset_id].interval.value] # then remove this interval group
            self.__del_timeframe(self.__assets[asset_id].interval) # remove this interval group in timeframes that we monitor as this was last one
        del self.__assets[asset_id]
    
    def get_asset_list(self):
        return self.__assets.values()
    
    def get_grouped_assets(self, group):
        return self.__grouped_assets[group]
        
    def is_listed(self,asset_id):
        if asset_id in self.__assets:
            return True
        else:
            return False  
    
    def get_updated_timeframes(self):
        timeframes_updated=[] # this list will contain interval enum values for which new data is available
        dt_now=dt.now()
        for inter, dt_next_update in self.__update_times.items(): # go through all the interval/timeframes for which we have assets to monitor
            if dt_now >= dt_next_update: # if present time is greater than the time when next sample should become available
                self.__update_times[inter] = dt_next_update + self.__timeframes[inter] # change the time to next update datetime (result will be datetime object)
                timeframes_updated.append(inter)
        
        return timeframes_updated
    
    def get_timeout_dt(self):
        if not self.__update_times: # if dict is empty meaning we are not monitoring any assets at the moment
            return None 
        
        closest_dt=None # temporary variable used to sort out the closest datetime to present datetime
        for dt_next_update in self.__update_times.values():
            if closest_dt is None: # with first sample there is nothing to compare with 
                closest_dt=dt_next_update
                continue
            elif closest_dt > dt_next_update: # all the following samples will be compared with the previous sample
                closest_dt=dt_next_update
                
        return closest_dt # return the closest datetime; returns a datetime object
    
    def get_lock(self, timeout=-1):
        self.__lock.acquire(timeout=timeout)
    
    def drop_lock(self):
        self.__lock.release()
    
    def islocked(self):
        return self.__lock.locked()
    
    def add_queue(self, asset_id, queue):
        return self.__assets[asset_id].add_queue(queue)
    
    def get_queue(self, asset_id, queue_id):
        if asset_id not in self.__assets: # the asset might have already been removed if it was used by only one testrun (in testrun.close_testrun method)
            return None
        else:
            return self.__assets[asset_id].get_queue(queue_id)
        
    def del_queue(self, asset_id, queue_id):
        return self.__assets[asset_id].del_queue(queue_id)
        
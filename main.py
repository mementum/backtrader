'''

'''
import threading
import backtrader as bt
import traceback
from datetime import datetime as dt
from tvDatafeed import Interval

from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
from strategyRunner.strategyRunner import strategyRunner as strategy_runner
from SQL.sqlManager import sqlManager, testrun, orders, operations, packet

def terminal(queue):
    while True:
        pack=queue.get()
        # print out info from data
        order=pack.get_data()
        print("Order "+order.state+" with entry price "+str(order.entry_price)+" and close price "+str(order.close_price))

# this strategy opens and closes orders in sequence to test the tradeTester
class MyStrategy(bt.Strategy):
    params = (
        ("sql_input", None),
        ("TUID", None),
        )
    
    def __init__(self):
        self.orders=orders(self.p.TUID)
        self.order=None

    def next(self):
        if self.order: # if order already created then close it
            self.order.close_order(str(dt.now().strftime("%d-%m-%y %H:%M")), self.data.close[0], 10000.0)
            pack=packet(operations.close_order, self.order.TUID, self.order)
            self.p.sql_input.put(pack)
            self.order=None
        else: # if not then open new order
            self.order=self.orders.new_order(str(dt.now().strftime("%d-%m-%y %H:%M")), "B/S", self.data.open[0], 100.0, 90.0, 110.0, 10000.0)
            pack=packet(operations.open_order, self.order.TUID, self.order)
            self.p.sql_input.put(pack)
        
    def notify_data(self, data, status, *args, **kwargs):
        if status == data.LIVE:
            print("live data")
        elif status == data.DELAYED:
            print("DELAYED data")

class controller(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.data_collector=tdr()
        self.sql=sqlManager() 
        self.sql_input, self.sql_output=self.sql.get_io()
        self.sql.start()
       
        self.testruns={} # this dictionary is used to keep track of all the testruns that are running
        # self.ident=self.get_id_num()
        
        threading.Thread.__init__(self)
        
    def run(self):
        while True:
            pass
    
    def exception_handler(self, e):
        traceback.print_exception(e)
    
    def add_testrun(self, strat_name, strategy, symbol, exchange, interval, account_size):
        '''
        Interval must come from the strategy file in __init__ because some strategies might have multiple intervals
        '''
        asset_id=self.data_collector.add_symbol(symbol, exchange, interval)
        start_dt_str=str(dt.now().strftime("%d-%m-%y %H:%M")) # opposite operation is datetime_obj=dt.strptime(start_dt_str,"%d-%m-%y %H:%M")
        testr=testrun(strat_name, start_dt_str, symbol, exchange, str(interval), asset_id, account_size)
        testr=self.sql.add_testrun(testr)
        TUID=testr.get_TUID()
        self.sql.set_streamer(TUID, asset_id)
        # start the actual testrun
        strat_ref=strategy_runner(self.data_collector, self.sql_input, TUID, asset_id, strategy, self.exception_handler) # SOMEHOW HAVE TO ENTER THE SQL_INPUT FOR STRATEGY INSTANCE
        strat_ref.start()
        self.testruns[strat_name]={asset_id, TUID, strat_ref}
    
    def del_testrun(self):
        pass
    
    def get_id_num(self):
        # tie ID number with asset_id and strategy and testrun name (set by user)
        pass
    

if __name__ == "__main__":
    contr=controller()
    contr.start()
    contr.add_testrun("test_strat1", MyStrategy, "ETHUSDT", "KUCOIN", Interval.in_1_minute, 10000) # strategy name must be unique and orders for that testrun must be removed from DB before running
    terminal(contr.sql_output)
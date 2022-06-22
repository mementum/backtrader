'''

'''
import threading
import backtrader as bt
import traceback
import time
from datetime import datetime as dt
from tvDatafeed import Interval

from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
from strategyRunner.strategyRunner import strategyRunner as strategy_runner
from SQL.sqlManager import sqlManager, testruns, orders, operations, packet
from controller.controller import controller

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

if __name__ == "__main__":
    contr=controller()
    #contr.start()
    contr.add_testrun("test_strat11", MyStrategy, "ETHUSDT", "KUCOIN", Interval.in_1_minute, 10000) # strategy name must be unique and orders for that testrun must be removed from DB before running
    t=threading.Thread(target=terminal, args=(contr.sql_output,))
    print("Thread started, waiting...")
    time.sleep(130)
    print("Deleting testrun")
    contr.del_testrun("test_strat11")
    print("Waiting...")
    time.sleep(300)
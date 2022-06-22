import threading
import traceback
from datetime import datetime as dt

from tvDatafeed.tvDatafeedRealtime import tvDatafeedRealtime as tdr
from strategyRunner.strategyRunner import strategyRunner as strategy_runner
from SQL.sqlManager import sqlManager, testruns

class controller(threading.Thread):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.data_collector=tdr()
        self.testruns=testruns(self.data_collector) 
        self.sql=sqlManager() 
        self.sql_input, self.sql_output=self.sql.get_io()
        self.sql.start()

        threading.Thread.__init__(self)
        
    def run(self):
        while True:
            pass
    
    def exception_handler(self, e):
        traceback.print_exception(e)
    
    def add_testrun(self, strat_name, strategy, symbol, exchange, interval, account_size):
        testrun=self.testruns.new_testrun(strat_name, symbol, exchange, interval, account_size)
        testrun=self.sql.add_testrun(testrun) # method will return a testrun object where some attributes are filled
        TUID=testrun.get_TUID() # TODO: testrun class must have get_streamer_info() method which returns asset_id and TUID (in a list)
        asset_id=testrun.get_asset_id()
        self.sql.set_streamer(TUID, asset_id) 
        strat_ref=strategy_runner(self.data_collector, self.sql_input, TUID, asset_id, strategy, self.exception_handler) # SOMEHOW HAVE TO ENTER THE SQL_INPUT FOR STRATEGY INSTANCE
        strat_ref.start()
        testrun.add_strat_ref(strat_ref)
    
    def del_testrun(self, strat_name):
        testrun=self.testruns.get_testrun(strat_name) # get the testrun object
        testrun.close_testrun() # change testrun object state to closed and if this was only testrun using this asset_set then that will be removed from data_collector as well
        self.sql.close_testrun(testrun) # close testrun in database and also close streamer
        testrun.get_strat_ref().stop() # stop the strategyRunner instance for this strategy
    
    def get_id_num(self):
        # tie ID number with asset_id and strategy and testrun name (set by user)
        pass

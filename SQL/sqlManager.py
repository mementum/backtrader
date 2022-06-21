'''
CONTINUE:
- create a prototype GUI design
- think from start (adding testrun) to finish on how the user is going to use this
- Modify the SQL query strings and methods
- create a method set_ticker_streamer() which is similar to set_streamer, but in it we specify (using ID number) which
  ticker data will be propagated to output_queue together with order data 

'''

import sqlite3, threading, queue
from enum import Enum

class orders(object):
    
    def __init__(self, TUID, order_id_starting=0): # user can specify the starting value for order_id (incase we are going from backtest to forward test)
        self.order_id=order_id_starting
        self.TUID=TUID
    
    def __next__(self):
        new_order_id=self.order_id
        self.order_id += 1
        return new_order_id
    
    def new_order(self, open_datetime, order_type, entry_price, position_size, stop_loss_price, take_profit_price, open_account_size): 
        new_order_id=self.__next__()  
        new_order=order(new_order_id, self.TUID, open_datetime, order_type, entry_price, position_size, stop_loss_price, \
                        take_profit_price, open_account_size)
        
        return new_order
        
class order(object):
    
    def __init__(self, order_id, TUID, open_datetime, order_type, entry_price, position_size, stop_loss_price, \
                 take_profit_price, open_account_size):
        self.order_id=order_id # this must be iterator and is automatically iterated
        self.TUID=TUID
        self.state="OPEN" # maybe we can use enumerator here?
        self.open_datetime=open_datetime # this will be datetime type
        self.close_datetime="NULL"
        self.order_type=order_type
        self.entry_price=entry_price
        self.close_price="NULL"
        self.position_size=position_size
        self.stop_loss_price=stop_loss_price
        self.take_profit_price=take_profit_price
        self.open_account_size=open_account_size
        self.close_account_size="NULL"
    
    def close_order(self, close_datetime, close_price, close_account_size):
        self.close_datetime=close_datetime
        self.close_price=close_price
        self.close_account_size=close_account_size
        self.state="CLOSED"
    
    def get_sql_params(self): # this method returns a valid SQL parameters tuple
        if self.state == "OPEN":
            return (self.order_id, self.TUID, self.state, self.open_datetime, self.close_datetime, \
                    self.order_type, self.entry_price, self.close_price, self.position_size, self.stop_loss_price, \
                    self.take_profit_price, self.open_account_size, self.close_account_size)
        else:
            return (self.state, self.close_datetime, self.close_price, self.close_account_size, self.TUID, self.order_id)
    
    def get_id(self):
        return self.TUID

class testrun(object):
    
    def __init__(self, strategy_name, start_datetime, symbol, exchange, interval, asset_id, starting_account):
        self.TUID=None
        self.strategy_name=strategy_name
        self.state="OPEN"
        self.start_datetime=start_datetime
        self.close_datetime="NULL"
        self.symbol=symbol
        self.exchange=exchange
        self.interval=interval
        self.asset_id=asset_id
        self.starting_account=starting_account
        self.closing_account="NULL"
    
    def close_testrun(self, close_datetime, closing_account):
        self.state="CLOSED"
        self.close_datetime=close_datetime
        self.closing_account=closing_account
    
    def get_sql_params(self):
        if self.state == "OPEN":
            return (self.strategy_name, self.state, self.start_datetime, self.close_datetime, self.symbol, \
                    self.exchange, self.interval, self.starting_account, self.closing_account)
        else:
            return (self.state, self.close_datetime, self.closing_account, self.TUID)
    
    def set_TUID(self, TUID):
        self.TUID=TUID
    
    def get_TUID(self):
        return self.TUID
    
    def get_asset_id(self):
        return self.asset_id

class operations(Enum):
    open_order=1
    close_order=2
    save_ticker_data=3
        
class packet(object):
    
    def __init__(self, op=None, ident=None, data=None):
        self.operation=op # use operations class instance to define which operation to perform
        self.ident=ident # either TUID (order packet) or asset_id (ticker data packet)
        self.data=data # order or ticker data
    
    def get_id(self):
        return self.ident
    
    def set_id(self, ident):
        self.ident=ident
    
    def get_operation(self):
        return self.operation
    
    def set_operation(self, op):
        self.operation=op
        
    def get_data(self):
        return self.data
    
    def add_data(self,data):
        self.data=data

class sqlDatabase(object):
    
    def __init__(self, path): # need to specify full path (with database name) to where database should be - if it isn't there then it will be created
        self.db_con=sqlite3.connect(path, check_same_thread=False) # application must make sure that writing to DB is serialized
        self.db_cursor=self.db_con.cursor()
        # check if we have "testruns" table created in this database already 
        self.db_cursor.execute('SELECT name from sqlite_master WHERE type = "table" AND name = "testruns"')
        # if not then create both tables "testruns" and "orders"
        if not self.db_cursor.fetchall(): # if list if empty then tables do not exist
            self._query_create_tables()
    
    def close(self):
        self.db_con.commit() # commit whatever changes wqe might have unsaved
        self.db_con.close() # close the connection
        
    def _query_create_tables(self):
        self.db_cursor.execute("CREATE TABLE testruns (TUID INTEGER PRIMARY KEY, \
                                                        strategy_name TEXT NOT NULL, \
                                                        state TEXT NOT NULL, \
                                                        start_datetime TEXT NOT NULL, \
                                                        close_datetime TEXT, \
                                                        symbol TEXT NOT NULL, \
                                                        exchange TEXT NOT NULL, \
                                                        interval TEXT NOT NULL, \
                                                        starting_account REAL, \
                                                        closing_account REAL)")
        
        self.db_cursor.execute("CREATE TABLE orders (order_id INTEGER NOT NULL, \
                                                    TUID INTEGER REFERENCES testruns, \
                                                    state INTEGER NOT NULL, \
                                                    open_datetime TEXT NOT NULL, \
                                                    close_datetime TEXT, \
                                                    order_type TEXT NOT NULL, \
                                                    entry_price REAL NOT NULL, \
                                                    close_price REAL, \
                                                    position_size REAL NOT NULL, \
                                                    stop_loss_price REAL NOT NULL, \
                                                    take_profit_price REAL NOT NULL, \
                                                    open_account_size REAL NOT NULL, \
                                                    close_account_size REAL, \
                                                    PRIMARY KEY(TUID, order_id))")
        
        self.db_con.commit()
        
    def query_insert_testrun(self, testrun_data): # this method returns TUID (row_id) of the newly added testrun
        # create a new row in testruns table
        self.db_cursor.execute("INSERT INTO testruns VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)", testrun_data) # testrun_data must be a tuple
        self.db_con.commit()
        # get the auto-incremented TUID value
        self.db_cursor.execute("SELECT * FROM testruns WHERE strategy_name = ?", (testrun_data[0],))
        return self.db_cursor.fetchall()[0][0] # fetchall returns a list of tuples; we select the first element from the first tuple
    
    def query_insert_order(self, order_data):
        self.db_cursor.execute("INSERT INTO orders VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", order_data) # order_data must be a tuple 
        self.db_con.commit()
    
    def query_update_testrun(self, testrun_data):
        self.db_cursor.execute("UPDATE testruns SET state = (?), close_datetime = (?), closing_account = (?) WHERE TUID = (?)",testrun_data)
        self.db_con.commit()
    
    def query_update_order(self, order_data): # order_data must specify TUID and order_id pair to identify the correct row in orders table
        self.db_cursor.execute("UPDATE orders SET state = (?), close_datetime = (?), close_price = (?), close_account_size = (?) WHERE TUID = (?) AND order_id = (?)",order_data)
        self.db_con.commit()
        
    def query_read_orders(self, testrun_ID):
        self.db_cursor.execute("SELECT * FROM testruns WHERE TUID = ?",testrun_ID)
        return self.db_cursor.fetchall()
    
    def query_read_testruns(self):
        self.db_cursor.execute("SELECT * FROM testruns")
        return self.db_cursor.fetchall()
    
class sqlManager(threading.Thread):

    def __init__(self):
        '''
        Constructor
        '''
        self.database=sqlDatabase(r"C:\Users\User\Documents\Projektid\Python\tradeTester\development materials\test_db.db") # user should be able to provide the path for this ???
        threading.Thread.__init__(self)
        self.run_mode=threading.Event()
        self.run_mode.set() # until this event is cleared we will run this thread
        self.active_listen=None
        self.lock=threading.Lock()
        self.input_queue=queue.Queue() # all strategies and data collector will place their data onto this queue for manager to process
        self.output_queue=queue.Queue() # this will go to GUI for sending data streams
        
    def get_io(self):
        return [self.input_queue, self.output_queue] 
    
    def run(self):
        while self.run_mode.isSet():
            packet=self.input_queue.get()
            self.get_lock()
            self.process_block(packet)
            self.drop_lock()
        
        self.database.close() # close the database connection
    
    def process_block(self, packet): # this method reads the operation type and based on that performs it; valid operations: create_testrun, close_testrun, open_order, close_order
        #sender=packet.get_id() # get senders ID                 
        op=packet.get_operation() # get the oepration type
        data=packet.get_data()
        sender=packet.get_id()
        
        if op is operations.open_order:
            sql_params=data.get_sql_params()
            self.database.query_insert_order(sql_params) 
        elif op is operations.close_order:
            sql_params=data.get_sql_params()
            self.database.query_update_order(sql_params)
        elif op is operations.save_ticker_data:
            # collect all data from packet, generate an sql_query string and save it into database
            pass
        
        if sender in self.active_listen: # if the packet was from Strategy that we are actively monitoring then pass that along to the GUI
            self.output_queue.put(packet)
    
    def get_lock(self, timeout=-1):
        self.lock.acquire(timeout=timeout)
    
    def drop_lock(self):
        self.lock.release()
    
    def add_testrun(self, testrun):
        sql_params=testrun.get_sql_params()
        self.get_lock() # as thread might be running at the same time then lock the resource before continuing
        TUID=self.database.query_insert_testrun(sql_params)
        # self.active_listen=TUID # save the TUID for which testrun we are actively forwarding (streaming) order (and in future ticker) data
        self.drop_lock()
        testrun.set_TUID(TUID)
        return testrun
    
    # write this as a direct method called by controller
    def read_testruns(self): # this function returns all the orders which are newly added
        testruns=self.database.query_read_testruns()
        testruns_packet=packet(operations.read_testruns, testruns)
        self.output_queue.put(testruns_packet) # send the packet to GUI
    
    # write this as a direct method called by controller
    def read_orders(self, sender, TUID): # this function returns all the orders which are newly added
        orders=self.database.query_read_orders(TUID)
        reply_packet=packet(operations.read_orders, sender, orders)
        self.output_queue.put(reply_packet) # send the packet to GUI
    
    # write this as a direct method called by controller
    def set_streamer(self, TUID, asset_id):
        self.get_lock() # as thread might be running at the same time then lock the resource before continuing
        self.active_listen=[TUID, asset_id] # save the TUID for which testrun we are actively forwarding (streaming) order (and in future ticker) data
        self.drop_lock()
    
    def stop(self):
        self.run_mode.clear() # clear the flag - this will stop running the main while loop  
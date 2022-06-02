'''
CONTINUE:

Test database manager methods and streaming functionality 

Write a simple controller module which handles eceptions that might raise when running invalid strategies
'''

import sqlite3, threading, queue
from sqlite3 import Error
from SQL.connection import operations as operations
from SQL.connection import packet as Packet

class sqlDatabase(object):
    
    def __init__(self, path): # need to specify full path (with database name) to where database should be - if it isn't there then it will be created
        self.db_con=sqlite3.connect(path)
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
                                                        start_datetime TEXT NOT NULL, \
                                                        close_datetime TEXT, \
                                                        symbol TEXT NOT NULL, \
                                                        exchange TEXT NOT NULL, \
                                                        interval TEXT NOT NULL, \
                                                        starting_account REAL)")
        
        self.db_cursor.execute("CREATE TABLE orders (order_id INTEGER PRIMARY KEY, \
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
                                                    close_account_size REAL)")
        
        self.db_con.commit()
        
    def query_insert_testrun(self, testrun_data):
        self.db_cursor.execute("INSERT INTO testruns VALUES(NULL, ?, ?, ?, ?, ?, ?, ?)", testrun_data) # testrun_data must be a tuple with proper values
        self.db_con.commit()
    
    def query_insert_order(self, order_data):
        self.db_cursor.execute("INSERT INTO orders VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", order_data) # testrun_data must be a tuple with proper values
        self.db_con.commit()
    
    def query_update_testrun(self, testrun_data):
        self.db_cursor.execute("UPDATE testruns SET close_datetime = (?) WHERE TUID = (?)",testrun_data)
        self.db_con.commit()
    
    def query_update_order(self, order_data):
        self.db_cursor.execute("UPDATE orders SET close_datetime = (?), close_price = (?), close_account_size = (?) WHERE order_id = (?)",order_data)
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
        return [self.input_queue, self.output_queue]
        
    def run(self):
        while self.run_mode.isSet():
            packet=self.input_queue.get()
            self.get_lock()
            self.process_block(packet)
            self.drop_lock()
        
        self.database.close() # close the database connection
    
    def process_block(self, packet): # this method reads the operation type and based on that performs it; valid operations: create_testrun, close_testrun, open_order, close_order
        sender=packet.get_id() # get senders ID                 
        op=packet.get_operation() # get the oepration type
        data=packet.get_data()
        
        if op is operations.open_testrun:
            self.database.query_insert_testrun(data) # simply create a new row in database
        elif op is operations.open_order:
            self.database.query_insert_order(data) 
        elif op is operations.close_testrun:
            self.database.query_update_testrun(data) 
        elif op is operations.close_order:
            self.database.query_update_order(data)
        elif op is operations.read_testruns:
            self.read_testruns(sender)
            return #in case or read he packet is from GUI so we can return right away
        elif op is operations.read_orders:
            self.read_orders(sender, data)
            return
        
        if self.active_listen == sender: # if the packet was from Strategy that we are actively monitoring then pass that along to the GUI
            self.output_queue.put(packet)
    
    def get_lock(self, timeout=-1):
        self.lock.acquire(timeout=timeout)
    
    def drop_lock(self):
        self.lock.release()
    
    def read_testruns(self, sender): # this function returns all the orders which are newly added
        testruns=self.database.query_read_testruns()
        reply_packet=Packet(operations.read_testruns, sender, testruns)
        self.output_queue.put(reply_packet) # send the packet to GUI
    
    def read_orders(self, sender, TUID): # this function returns all the orders which are newly added
        orders=self.database.query_read_orders(TUID)
        reply_packet=Packet(operations.read_orders, sender, orders)
        self.output_queue.put(reply_packet) # send the packet to GUI
    
    def set_streamer(self, TUID):
        self.get_lock() # as thread might be running at the same time then lock the resource before continuing
        self.active_listen=TUID # save the TUID for which testrun we are actively forwarding (streaming) order (and in future ticker) data
        self.drop_lock()
    
    def stop(self):
        self.run_mode.clear() # clear the flag - this will stop running the main while loop  
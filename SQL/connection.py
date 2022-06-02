'''
SPECS:
- Need to be able to write and read from database from different threads
- Database will contain order data: entry price, position size, s/l price, t/p price, status (open/closed)
- Order data must be separate into separate groups based on strategy name - each strategy has their own order data

IMPLEMENTATION OPTIONS:
- ZeroMQ
- Rest API

IMPLEMENTATION:
We will have a SQL database that only this class instance can access. This class will implement a API over sockets to which other python 
programs can connect to and then send and retrieve data. 

Each new connection will have a class which listens to incoming request, interprets it and then request that data from sqlManager class by
sending a queryRequest over queue to teh sqlManager. The queryRequest is a class in which we specify the action (read or write data) and 
address (strategy name and instance - so in theory we can have multiple identical strategies running). The sqlManager will respond with queryResponse
which is a class in which we give the actual data

WE DONT ACTUALLY NEED TO USE SOCKET CONNECTIONS ?! WE CAN AVOID WHOLE PROGRAM CRASH BY USING TRY STATEENTS INSIDE THE STARTEGY THREADS; IF THERE IS AN EXCEPTION THEN SIMPLY PUT SIGNAL ON ERROR QUEUE AND CLOSE THREAD
'''

# import socket, threading
from enum import Enum

class operations(Enum):
    open_testrun=1
    open_order=2
    close_testrun=3
    close_order=4
    read_testruns=5
    read_orders=6

class packet(object):
    
    def __init__(self, op=None, ident=None, data=None):
        self.operation=op # use operations class instance to define which operation to perform
        self.ident=ident # who sent the data - GUI, strategies and data collector will all have unique ID number. When this class instance is received they will check if this is for the by that number
        self.data=data # this contanis the data to be written or that has been read - it can be a tuple or a list of tuples (in future maybe use Pandas?)
    
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
    
# class connectionHandler(threading.Thread):
#
#     def __init__(self, conn, addr):
#         self.conn=conn
#         self.addr=addr
#         threading.Thread.__init__(self)
#
#     def run(self):
#         pass
#
# class connectionsReceiver(threading.Thread):
#
#     def __init__(self):
#         self.host="127.0.0.1"
#         self.port=50000
#         self.close=threading.Event()
#         threading.Thread.__init__(self)
#
#     def run(self):
#         self.__listener_thread=threading.Thread(target=self.listener)
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
#             self.__sock.bind((self.host, self.port))
#             self.__sock.listen()
#             while not self.close.is_set():
#                 conn, addr=self.sock.accept() # receive a new connection
#                 connectionHandler(conn, addr)
#
#     def stop(self):
#         self.close.set()
            
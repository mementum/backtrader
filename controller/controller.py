'''
TODO:
- investiagte how to safely separate strategyRunner threads from rest of teh system so in case there is any kind of error and thread crashes
  then the whole program does not crash and it is able to detect this and show to this user and recover from this.
'''

class controller(object):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        
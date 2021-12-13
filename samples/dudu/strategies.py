from datetime import date
import datetime

import backtrader as bt
import backtrader.indicators as btind
from backtrader.order import Order
from transactionsLoader import *





class OldStrategy(bt.Strategy):
    '''
    Current transactions based on our history log
    '''
    params = (('symbol', ''), ('priceSize', 1),)
    

    def findTransaction(self, transactionDate, transactionIndex):
        #for trans in self.pastTransactions:
        trans = self.pastTransactions[transactionIndex]
        if int(transactionDate) == bt.date2num(trans.transactionDate):
            return trans
        return None

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datadate = self.datas[0].datetime 
        self.transactionIndex=0
        
        self.pastTransactions = TransactionsLoader.Load(self.p.symbol)
        

        # Keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price*self.p.priceSize,
                          order.executed.value*self.p.priceSize,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl*self.p.priceSize, trade.pnlcomm))

    def next(self):

        if self.order:
            return
        
        #dt = bt.num2date(self.datadate[0])
        #if not self.position:
        trans = self.findTransaction(self.datadate[0], self.transactionIndex)
        # Not yet in the market... we MIGHT BUY if...
        if trans:
            if trans.transactionType == 'buy':
                self.log('BUY CREATE, %.2f, Amount: %.2f' % (trans.price * self.p.priceSize,trans.amount))
                self.order = self.buy(exectype=Order.Limit,price=trans.price,size=trans.amount)
                self.transactionIndex = self.transactionIndex + 1

        if self.position:
            #trans = self.findTransaction(self.datadate[0])
            # Already in the market... we might sell
            if trans:
                if trans.transactionType == 'sell':
                    self.log('SELL CREATE, %.2f, Amount: %.2f' % (trans.price * self.p.priceSize,trans.amount))

                    # Keep track of the created order to avoid a 2nd order
                    self.order = self.sell(exectype=Order.Limit,price=trans.price,size=trans.amount)
                    self.transactionIndex = self.transactionIndex + 1


class TestStrategy(bt.Strategy):
    '''
    Buy when there are two consecutive red bars and sell five bars later
    '''

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Commission: %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):

        if self.order:
            return

        if not self.position:
            # Not yet in the market... we MIGHT BUY if...
            if self.dataclose[0] < self.dataclose[-1]:
                if self.dataclose[-1] < self.dataclose[-2]:
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.order = self.buy()
        else:
            # Already in the market... we might sell
            if len(self) >= (self.bar_executed + 5):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


class SMAcrossover(bt.Strategy):
    params = (('fast', 20), ('slow', 50),)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        #print(f'{dt.isoformat()} {txt}') # Comment this line when running optimization

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

        fast_sma, slow_sma = bt.ind.SMA(period=self.p.fast), bt.ind.SMA(period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(fast_sma, slow_sma)
        #self.signal_add(bt.SIGNAL_LONGSHORT, bt.ind.CrossOver(sma1, sma2))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # An active Buy/Sell order has been submitted/accepted - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, {order.executed.price:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset orders
        self.order = None

    def next(self):
        # Check for open orders
        if self.order:
            return

        if self.crossover > 0:
            self.log(f'BUY CREATE {self.dataclose[0]:.2f}')
            self.order = self.buy()
        elif self.crossover < 0:
            self.log(f'SELL CREATE {self.dataclose[0]:.2f}')
            self.order = self.sell()


class EmaCrossLongShort(bt.Strategy):
    '''This strategy buys/sells upong the close price crossing
    upwards/downwards an Exponential Moving Average.
    It can be a long-only strategy by setting the param "longonly" to True
    '''
    params = dict(
        fast=13,
        slow=48,
        printout=True,
        longonly=False,
    )

    def log(self, txt, dt=None):
        if self.p.printout:
            dt = dt or self.data.datetime[0]
            dt = bt.num2date(dt)
            print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.orderid = None  # to control operation entries

        fast_ema, slow_ema = btind.MovAv.EMA(period=self.p.fast), btind.MovAv.EMA(period=self.p.slow)
        self.signal = btind.CrossOver(fast_ema, slow_ema)
        self.log(f'Initial portfolio value of {self.broker.get_value():.2f}\n')

    def start(self):
        pass

    def next(self):
        if self.orderid:
            return  # if an order is active, no new orders are allowed

        if self.signal > 0.0:  # cross upwards
            if self.position:
                self.log(f'CLOSE SHORT position of {abs(self.position.size)} shares '
                         f'at {self.data.close[0]:.2f}')
                self.close()

            self.log(f'BUY {self.getsizing()} shares at {self.data.close[0]}')
            self.buy()

        elif self.signal < 0.0:
            if self.position:
                self.log(f'CLOSE LONG position of {self.position.size} shares '
                         f'at {self.data.close[0]:.2f}')
                self.close()

            if not self.p.longonly:
                self.log(f'SELL {abs(self.getsizing())} shares at '
                         f'{self.data.close[0]}')
                self.sell()

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return  # Await further notifications

        if order.status == order.Completed:
            if order.isbuy():
                buytxt = f'BUY COMPLETED. ' \
                         f'Size: {order.executed.size}, ' \
                         f'Price: {order.executed.price:.2f}, ' \
                         f'Commission: {order.executed.comm:.2f}'
                self.log(buytxt, order.executed.dt)
            else:
                selltxt = 'SELL COMPLETED. ' \
                         f'Size: {abs(order.executed.size)}, ' \
                         f'Price: {order.executed.price:.2f}, ' \
                         f'Commission: {order.executed.comm:.2f}'
                self.log(selltxt, order.executed.dt)

        elif order.status in [order.Expired, order.Canceled, order.Margin]:
            self.log(f'{order.Status[order.status]}')
            pass  # Simply log

        # Allow new orders
        self.orderid = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'TRADE COMPLETED, '
                     f'Portfolio: {self.broker.get_value():.2f}, '
                     f'Gross: {trade.pnl:.2f}, '
                     f'Net: {trade.pnlcomm:.2f}')

        elif trade.justopened:
            #self.log('TRADE OPENED, SIZE %2d' % trade.size)
            pass
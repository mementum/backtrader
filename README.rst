backtrader
==========
BackTesting platform written in Python to test trading strategies.

Read the full documentation at: `backtrader documentation http://backtrader.readthedocs.org/en/latest/introduction.html`_

Installation
============
From pypi:

  - pip install backtrader

Or run directly from source by placing the *backtrader* directory found in the sources inside your project

Features:
=========
  - Bar/Tick based approach

    Strategies/Indicators/Brokers will be called on each arriving bar

  - Data Feeds Supported

    Yahoo Online and CSV
    Another example of CSV is given

  - Indicators on Data Feeds or on Indicators

  - Broker (attempting a realistic order execution simulation)

    With definable Commission schemes per assets and/or globally

  - Plotting

    Per strategy plot of datas, indicators and results (actual shown items are tunable)

  - Analyzer (basic)

    As the name implies there is an analysis of the performance of the strategy

Alternatives
============
If after seeing the docs (see also the example below) you feel this is not your cup of tea, you can always have a look at similar Python platforms:

  - `PyAlgoTrade https://github.com/gbeced/pyalgotrade`_
  - `Zipline https://github.com/quantopian/zipline`_
  - `Ultra-Finance https://code.google.com/p/ultra-finance/`_
  - `ProfitPy https://code.google.com/p/profitpy/`_

Example:
========
::
    import datetime
    import backtrader as bt

    class TestStrategy(bt.Strategy):
        params = (('maperiod', 15),)

        def log(self, txt, dt=None):
            dt = dt or self.data.datetime[0]
            print '%s, %s' % (dt.isoformat(), txt)

        def __init__(self):
	    self.orderid = None
            self.data = self.datas[0]
            self.dataclose = self.data.close
            self.sma = bt.indicators.MovingAverageSimple(self.data, period=self.params.maperiod)

        def ordernotify(self, order):
            if order.status == bt.Order.Completed:
                if isinstance(order, bt.BuyOrder):
                    self.log('EXEC BUY , Price: %.2f, Size: %d' % \
                             (order.executed.price, order.executed.size), order.executed.dt)
                else: # elif isinstance(order, SellOrder):
                    self.log('EXEC SELL , Price: %.2f, Size: %d' % \
                             (order.executed.price, order.executed.size), order.executed.dt)

                # Allow new orders
                self.orderid = None

        def next(self):
            if self.orderid:
                return # if an order is active, no new orders are allowed

            if not self.position.size:
                if self.dataclose[0] > self.sma[0][0]:
                    self.log('BUY CREATE , %.2f' % self.dataclose[0])
                    self.orderid = self.buy()

            elif self.dataclose[0] < self.sma[0][0]:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.orderid = self.sell()


    # Create a Cerebro Engine, feed a data souce, a strategy and rund
    cerebro = bt.Cerebro()

    data = bt.feeds.YahooFinanceCSVData(dataname='./datas/yahoo/oracle-2000.csv', reversed=True)

    cerebro.adddata(data)
    cerebro.addstrategy(TestStrategy, maperiod=15) # same as default
    cerebro.broker.setcash(1000.0)
    print 'Starting Portfolio Value: %.2f' % cerebro.broker.getvalue()
    cerebro.run()
    print 'Final Portfolio Value: %.2f' % cerebro.broker.getvalue()
    cerebro.plot() # matplotlib is needed for this to work

Strategy
########

A ``Cerebro`` instance is the pumping heart and controlling brain of
``backtrader``. A ``Strategy`` is the same for the platform user.

The *Strategy's* expressed lifecycle in methods

  0. Conception: ``__init__``

     This is obviously invoked during instantiation: ``indicators`` will be
     created here and other needed attribute. Example::

       def __init__(self):
           self.sma = btind.SimpleMovingAverage(period=15)

     .. note::

	A strategy can be interrupted during *birth* by raising a
	``StrategySkipError`` exception from the module ``backtrader.errors``

	This will avoid going through the strategy during a backtesting. See
	the section ``Exceptions``

  1. Birth: ``start``

     The world (``cerebro``) tells the strategy is time to start kicking. A
     default empty method exists.

  2. Childhood: ``prenext``

     ``indicators`` declared during conception will have put constraints on how
     long the strategy needs to mature: this is called the ``minimum
     period``. Above ``__init__`` created a *SimpleMovingAverage* with a
     ``period=15``.

     As long as the syste has seen less than ``15`` bars, ``prenext`` will be
     called (there is a default method which is a no-op)

  3. Adulthood: ``next``

     Once the system has seen ``15`` bars and the ``SimpleMovingAverage`` has a
     buffer large enough to start producing values, the strategy is mature
     enough to really execute.

     There is a ``nextstart`` method which is called exactly *once*, to mark
     the switch from ``prenext`` to ``next``. The default implementation of
     ``nextstart`` is to simply call ``next``

  4. Reproduction: ``None``

     Ok, strategies do not really reproduce. But in a sense they do, because
     the system will instantiate them several times if *optimizing* (with
     different parameters)

  5. Death: ``stop``

     The system tells the strategy the time to come to a reset and put things
     in order has come. A default empty method exists.

In most cases and for regular usage patterns this will look like::

  class MyStrategy(bt.Strategy):

      def __init__(self):
          self.sma = btind.SimpleMovingAverage(period=15)

      def next(self):
          if self.sma > self.data.close:
	      # Do something
	      pass

	  elif self.sma < self.data.close:
	      # Do something else
	      pass


In this snippet:

  - During ``__init__`` an attribute is assigned an indicator
  - The default empty ``start`` method is not overriden
  - ``prenext`` and ``nexstart`` are not overriden
  - In ``next`` the value of the indicator is compared against the closing
    price to do something
  - The default empty ``stop`` method is not overriden


Strategies, like a trader in the real world, will get notified when events take
place. Actually once per ``next`` cycle in the backtesting process. The
strategy will:

  - be notified through ``notify_order(order)`` of any status change in an
    order

  - be notified through ``notify_trade(trade)`` of any
    opening/updating/closing trade

  - be notified through ``notify_cashvalue(cash, value)`` of the current cash
    and portfolio in the broker

  - be notified through ``notify_fund(cash, value, fundvalue, shares)`` of the
    current cash and portfolio in the broker and tradking of fundvalue and
    shares

  - Events (implementation specific) via ``notify_store(msg, *args, **kwargs)``

    See :doc:`cerebro` for an explanation on the *store* notifications. These
    will delivered to the strategy even if they have also been delivered to a
    ``cerebro`` instance (with an overriden ``notify_store`` method or via a
    *callback*)

And *Strategies* also like traders have the chance to operate in the market
during the ``next`` method to try to achieve profit with

  - the ``buy`` method to go long or reduce/close a short position
  - the ``sell`` method to go short or reduce/close a long position
  - the ``close`` method to obviously close an existing position
  - the ``cancel`` method to cancel a not yet executed order


How to Buy/Sell/Close
=====================

The ``Buy`` and ``Sell`` methods generate orders. When invoked they return an
``Order`` (or subclass) instance that can be used as a reference. This order
has a unique ``ref`` identifier that can be used for comparison

.. note:: Subclasses of ``Order`` for speficic broker implementations may carry
	  additional *unique identifiers* provided by the broker.

To create the order use the following parameters:

  - ``data`` (default: ``None``)

    For which data the order has to be created. If ``None`` then the
    first data in the system, ``self.datas[0] or self.data0`` (aka
    ``self.data``) will be used

  - ``size`` (default: ``None``)

    Size to use (positive) of units of data to use for the order.

    If ``None`` the ``sizer`` instance retrieved via ``getsizer`` will
    be used to determine the size.

  - ``price`` (default: ``None``)

    Price to use (live brokers may place restrictions on the actual
    format if it does not comply to minimum tick size requirements)

    ``None`` is valid for ``Market`` and ``Close`` orders (the market
    determines the price)

    For ``Limit``, ``Stop`` and ``StopLimit`` orders this value
    determines the trigger point (in the case of ``Limit`` the trigger
    is obviously at which price the order should be matched)

  - ``plimit`` (default: ``None``)

    Only applicable to ``StopLimit`` orders. This is the price at which
    to set the implicit *Limit* order, once the *Stop* has been
    triggered (for which ``price`` has been used)

  - ``exectype`` (default: ``None``)

    Possible values:

    - ``Order.Market`` or ``None``. A market order will be executed
      with the next available price. In backtesting it will be the
      opening price of the next bar

    - ``Order.Limit``. An order which can only be executed at the given
      ``price`` or better

    - ``Order.Stop``. An order which is triggered at ``price`` and
      executed like an ``Order.Market`` order

    - ``Order.StopLimit``. An order which is triggered at ``price`` and
      executed as an implicit *Limit* order with price given by
      ``pricelimit``

  - ``valid`` (default: ``None``)

    Possible values:

      - ``None``: this generates an order that will not expire (aka
        *Good til cancel*) and remain in the market until matched or
        canceled. In reality brokers tend to impose a temporal limit,
        but this is usually so far away in time to consider it as not
        expiring

      - ``datetime.datetime`` or ``datetime.date`` instance: the date
        will be used to generate an order valid until the given
        datetime (aka *good til date*)

      - ``Order.DAY`` or ``0`` or ``timedelta()``: a day valid until
        the *End of the Session* (aka *day* order) will be generated

      - ``numeric value``: This is assumed to be a value corresponding
        to a datetime in ``matplotlib`` coding (the one used by
        ``backtrader``) and will used to generate an order valid until
        that time (*good til date*)

  - ``tradeid`` (default: ``0``)

    This is an internal value applied by ``backtrader`` to keep track
    of overlapping trades on the same asset. This ``tradeid`` is sent
    back to the *strategy* when notifying changes to the status of the
    orders.

  - ``**kwargs``: additional broker implementations may support extra
    parameters. ``backtrader`` will pass the *kwargs* down to the
    created order objects

    Example: if the 4 order execution types directly supported by
    ``backtrader`` are not enough, in the case of for example
    *Interactive Brokers* the following could be passed as *kwargs*::

      orderType='LIT', lmtPrice=10.0, auxPrice=9.8

    This would override the settings created by ``backtrader`` and
    generate a ``LIMIT IF TOUCHED`` order with a *touched* price of 9.8
    and a *limit* price of 10.0.


Information Bits:
=================

  - A Strategy has a *length* which is always equal to that of the main
    data (``datas[0]``) and can of course be gotten with ``len(self)``

    ``next`` can be called without changes in *length* if data is being
    replayed or a live feed is being passed and new ticks for the same
    point in time (length) are arriving


Member Attributes:
==================

  - ``env``: the cerebro entity in which this Strategy lives
  - ``datas``: array of data feeds which have been passed to cerebro

    - ``data/data0`` is an alias for datas[0]
    - ``dataX`` is an alias for datas[X]

    *data feeds* can also be accessed by name (see the reference) if one has been
    assigned to it

  - ``dnames``: an alternative to reach the data feeds by name (either with
    ``[name]`` or with ``.name`` notation)

    For example if resampling a data like this::

      ...
      data0 = bt.feeds.YahooFinanceData(datname='YHOO', fromdate=..., name='days')
      cerebro.adddata(data0)
      cerebro.resampledata(data0, timeframe=bt.TimeFrame.Weeks, name='weeks')
      ...

    Later in the strategy one can create indicators on each like this::

      ...
      smadays = bt.ind.SMA(self.dnames.days, period=30)  # or self.dnames['days']
      smaweeks = bt.ind.SMA(self.dnames.weeks, period=10)  # or self.dnames['weeks']
      ...

  - ``broker``: reference to the broker associated to this strategy
    (received from cerebro)

  - ``stats``: list/named tuple-like sequence holding the Observers created by
    cerebro for this strategy

  - ``analyzers``: list/named tuple-like sequence holding the Analyzers created
    by cerebro for this strategy

  - ``position``: actually a property which gives the current position for
    ``data0``.

    Methods to retrieve all possitions are available (see the reference)




Member Attributes (meant for statistics/observers/analyzers):
=============================================================

  - ``_orderspending``: list of orders which will be notified to the
    strategy before ``next`` is called

  - ``_tradespending``: list of trades which will be notified to the
    strategy before ``next`` is called

  - ``_orders``: list of order which have been already notified. An order
    can be several times in the list with different statuses and different
    execution bits. The list is menat to keep the history.

  - ``_trades``: list of order which have been already notified. A trade
    can be several times in the list just like an order.

.. note::

   Bear in mind that ``prenext``, ``nextstart`` and ``next`` can be called
   several times for the same point in time (ticks updating prices for the daily
   bar, when a daily timeframe is in use)


Reference: Strategy
===================

.. currentmodule:: backtrader

.. autoclass:: Strategy

   .. automethod:: next
   .. automethod:: nextstart
   .. automethod:: prenext

   .. automethod:: start
   .. automethod:: stop

   .. automethod:: notify_order
   .. automethod:: notify_trade
   .. automethod:: notify_cashvalue
   .. automethod:: notify_fund
   .. automethod:: notify_store

   .. automethod:: buy
   .. automethod:: sell
   .. automethod:: close
   .. automethod:: cancel

   .. automethod:: buy_bracket
   .. automethod:: sell_bracket

   .. automethod:: order_target_size
   .. automethod:: order_target_value
   .. automethod:: order_target_percent

   .. automethod:: getsizer
   .. automethod:: setsizer
   .. automethod:: getsizing

   .. automethod:: getposition
   .. automethod:: getpositionbyname
   .. automethod:: getpositionsbyname

   .. automethod:: getdatanames
   .. automethod:: getdatabyname

   .. automethod:: add_timer
   .. automethod:: notify_timer

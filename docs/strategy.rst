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


Information Bits:

  - A Strategy has a "length" which is always equal to that of the main
    data (datas[0])

    ``next`` can be called without changes in length if data is being
    replayed or a live feed is being passed and new ticks for the same
    point in time (length) are arriving

Member Attributes:

  - ``env``: the cerebro entity in which this Strategy lives
  - ``datas``: array of datas which have been passed to cerebro

    - ``data/data0`` is an alias for datas[0]
    - ``dataX`` is an alias for datas[X]

    *datas* can also be accessed by name (see the reference) if one has been
    assigned to it

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
==================

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

   .. automethod:: buy
   .. automethod:: sell
   .. automethod:: close

   .. automethod:: getsizer
   .. automethod:: setsizer
   .. automethod:: getsizing

   .. automethod:: getposition
   .. automethod:: getpositionbyname
   .. automethod:: getpositionsbyname

   .. automethod:: getdatanames
   .. automethod:: getdatabyname

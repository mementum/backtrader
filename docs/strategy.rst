Strategy
########

Strategies are the core of backtesting. Every single sample has a strategy. See
the reference below for doubts about member attributes/methods

Strategies are ``Lines`` objects but only an unnamed line is defined to
ensure the strategy can be synchronized to the main data.

Logic does usually involve Indicators. Indicators are defined in:

  - ``__init__``

The class will:

  - Be notified through ``notify_order(order)`` of any status change in an
    order

  - Be notified through ``notify_trade(trade)`` of any
    opening/updating/closing trade

  - Have its methods ``prenext``, ``nextstart`` and ``next`` invoked to
    execute the logic

Bits:

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

  - ``broker``: reference to the broker associated to this strategy
    (received from cerebro)

  - ``stats``: list/named tuple-like sequence holding the Observers created by
    cerebro for this strategy

  - ``analyzers``: list/named tuple-like sequence holding the Analyzers created
    by cerebro for this strategy

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


Reference: Srategy
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

   .. automethod:: buy
   .. automethod:: sell
   .. automethod:: close

   .. automethod:: getsizer
   .. automethod:: setsizer
   .. automethod:: getsizing

   .. automethod:: getposition

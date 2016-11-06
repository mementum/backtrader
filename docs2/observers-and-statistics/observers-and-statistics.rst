
Observers and Statistics
########################

Strategies running inside the ``backtrader`` do mostly deal with **data feeds**
and **indicators**.

Data feeds are added to **Cerebro** instances and end up being part of the
input of strategies (parsed and served as attributes of the instance) whereas
Indicators are declared and managed by the Strategy itself.

All ``backtrader`` sample charts have so far had 3 things plotted which seem to
be taken for granted because they are not declared anywhere:

  - Cash and Value (what's happening with the money in the broker)
  - Trades (aka Operations)
  - Buy/Sell Orders

They are ``Observers`` and exist within the submodule
``backtrader.observers``. They are there because **Cerebro** supports a
parameter to automatically add (or not) them to the Strategy:

  - ``stdstats`` (default: ``True``)

If the default is respected **Cerebro** executes the following equivalent user
code::

  import backtrader as bt

  ...

  cerebro = bt.Cerebro()  # default kwarg: stdstats=True

  cerebro.addobserver(bt.observers.Broker)
  cerebro.addobserver(bt.observers.Trades)
  cerebro.addobserver(bt.observers.BuySell)

Let's see the usual chart with those 3 default observers (even if no order is
issued and therefore no trade happens and there is no change to the cash and
portfolio value)

.. literalinclude:: ./observers-default.py
   :language: python
   :lines: 21-46

.. thumbnail:: ./observers-default.png

Now let's change the value of ``stdstats`` to ``False`` when creating the
**Cerebro** instance (can also be done when invoking ``run``)::

  cerebro = bt.Cerebro(stdstats=False)

The chart is different now.

.. thumbnail:: ./observers-default-false.png

Accesing the Observers
======================

The Observers as seen above are already there in the default case and collecting
information which can be used for statistical purposes and that's why acess to
the observers can be done through an attribute of the strategy called:

  - ``stats``

It is simply a placeholder. If we recall the addition of one of the default
**Observers** as laid out above::

  ...
  cerebro.addobserver(backtrader.observers.Broker)
  ...

The obvious question would be how to access the ``Broker`` observer. Here for
example how it's done from the ``next`` method of a strategy::

  class MyStrategy(bt.Strategy):

      def next(self):

          if self.stats.broker.value[0] < 1000.0:
	     print('WHITE FLAG ... I LOST TOO MUCH')
	  elif self.stats.broker.value[0] > 10000000.0:
	     print('TIME FOR THE VIRGIN ISLANDS ....!!!')

The ``Broker`` observer just like a Data, an Indicator and the Strategy itself
is also a ``Lines`` objects. In this case the ``Broker`` has 2 lines:

  - ``cash``
  - ``value``

Observer Implementation
=======================

The implementation is very similar to that of an Indicator::

  class Broker(Observer):
      alias = ('CashValue',)
      lines = ('cash', 'value')

      plotinfo = dict(plot=True, subplot=True)

      def next(self):
          self.lines.cash[0] = self._owner.broker.getcash()
          self.lines.value[0] = value = self._owner.broker.getvalue()

Steps:

  - Derive from ``Observer`` (and not from ``Indicator``)

  - Declare lines and params as needed (``Broker`` has 2 lines but no params)

  - There will be an automatic attribute ``_owner`` which is the strategy
    holding the observer

Observers come in action:

  - After all Indicators have been calculated
  - After the Strategy ``next`` method has been executed

  - That means: at the end of the cycle ... they **observe** what has happened

In the ``Broker`` case it's simply blindly recording the broker cash and
portfolio values at each point in time.

Adding Observers to the Strategy
================================

As already pointed out above, **Cerebro** is using the ``stdstats`` parameter to
decide whether to add 3 default **Observers**, alleviating the work of the end
user.

Adding other Observers to the mix is possible, be it along the ``stdstats`` or
removing those.

Let's go for the usual strategy which buys when the ``close`` price goes above a
``SimpleMovingAverage`` and sells if the opposite is true.

With one "addition":

  - **DrawDown** which is an already existing observer in the ``backtrader``
    ecosystem

.. literalinclude:: ./observers-default-drawdown.py
   :language: python
   :lines: 21-46

The visual output shows the evolution of the drawdown

.. thumbnail:: ./observers-default-drawdown.png

And part of the text output::

  ...
  2006-12-14T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-15T23:59:59+00:00, DrawDown: 0.22
  2006-12-15T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-18T23:59:59+00:00, DrawDown: 0.00
  2006-12-18T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-19T23:59:59+00:00, DrawDown: 0.00
  2006-12-19T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-20T23:59:59+00:00, DrawDown: 0.10
  2006-12-20T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-21T23:59:59+00:00, DrawDown: 0.39
  2006-12-21T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-22T23:59:59+00:00, DrawDown: 0.21
  2006-12-22T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-27T23:59:59+00:00, DrawDown: 0.28
  2006-12-27T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-28T23:59:59+00:00, DrawDown: 0.65
  2006-12-28T23:59:59+00:00, MaxDrawDown: 2.62
  2006-12-29T23:59:59+00:00, DrawDown: 0.06
  2006-12-29T23:59:59+00:00, MaxDrawDown: 2.62

.. note::

   As seen in the text output and in the code, the ``DrawDown`` observer has
   actually 2 lines:

     - ``drawdown``
     - ``maxdrawdown``

   The choice is not to plot the ``maxdrawdown`` line, but make it is still
   available to the user.

   Actually the last value of ``maxdrawdown`` is also available in a direct
   attribute (not a line) with the name of ``maxdd``

Developing Observers
====================

The implementation of the ``Broker`` observer was shown above. To produce a
meaningful observer, the implementation can use the following information:

  - ``self._owner`` is the currently strategy being executed

    As such anything within the strategy is available to the observer

  - Default internal things available in the strategy which may be useful:

    - ``broker`` -> attribute giving access to the broker instance the strategy
      creates order against

      As seen in ``Broker``, cash and portfolio values are collected by invoking
      the methods ``getcash`` and ``getvalue``

   - ``_orderspending`` -> list orders created by the strategy and for which the
     broker has notified an event to the strategy.

     The ``BuySell`` observer traverses the list looking for orders which have
     executed (totally or partially) to create an average execution price for
     the given point in time (index 0)

   - ``_tradespending`` -> list of trades (a set of completed buy/sell or
     sell/buy pairs) which is compiled from the buy/sell orders

An **Observer** can obviously access other observers over the
``self._owner.stats`` path.

Custom *OrderObserver*
----------------------

The standard ``BuySell`` observer does only care about operations which have
executed. We can create an observer which shows when orders where created and if
they expired.

For the sake of *visibility* the display will not be plotted along the price but
on a separate axis.

.. literalinclude:: ./orderobserver.py
   :language: python
   :lines: 21-

The custom observer only cares about **buy** orders, because this is a strategy
which only buys to try to make a profit. Sell orders are Market orders and will
be executed immediately.

The Close-SMA CrossOver strategy is changed to:

  - Create a Limit order with a price below 1.0% the close price at the moment
    of the signal

  - A validity for the order of 7 (calendar) days

The resulting chart.

.. thumbnail:: observers-orderobserver.png

Several orders have expired as can be seen in the new subchart (red squares) and
we can also appreciate that between "creation" and "execution" several days
happen to be.

Finally the code for this strategy which applies the new **observer**

.. literalinclude:: ./observers-orderobserver.py
   :language: python
   :lines: 21-

Saving/Keeping the statistics
=============================

As of now ``backtrader`` has not implemented any mechanism to track the values
of observers storing them into files. The best way to do it:

  - Open a file in the ``start`` method of the strategy

  - Write the values down in the ``next`` method of the strategy

Considering the ``DrawDown`` observer, it could be done like this

.. code-block:: python

  class MyStrategy(bt.Strategy):

      def start(self):

          self.mystats = open('mystats.csv', 'wb')
	  self.mystats.write('datetime,drawdown, maxdrawdown\n')

      def next(self):
          self.mystats.write(self.data.datetime.date(0).strftime('%Y-%m-%d'))
          self.mystats.write(',%.2f' % self.stats.drawdown.drawdown[-1])
          self.mystats.write(',%.2f' % self.stats.drawdown.maxdrawdown-1])
	  self.mystats.write('\n')

To save the values of index 0, once all observers have been processed a custom
observer which writes to a file could be added as the last observer to the
system to save values to a csv file.

.. note:: The :doc:`../writer` functionality can automate this task.

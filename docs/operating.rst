Operating the platform
######################

Line Iterators
**************

To engage into operations, the plaftorm uses the notion of `line
iterators`. They have been loosely modeled after Python's iterators but have
actually nothing to do with them.

Strategies and Indicators are `line iterators`.

The `line iterator` concept tries to describe the following:

  - A `Line Iterator` kicks slave `line iterators` telling them to iterate
  - A `Line Iterator` then iterates over its own declared named lines `setting`
    values

The key to iteration, just like with regular Python iterators, is:

  - The ``next`` method

    It will be called for each iteration. The ``datas`` array which the *line
    iterator* has and serve as basis for logic/calculations will have already
    been moved to the next index by the platform (barring `data replay`)

    Called when the **minimum period** for the `line iterator` has been met. A
    bit more on this below.

But because they are not regular iterators, two additional methods exist:

  - ``prenext``

    Called before the **minimum period** for the `line iterator`` has been met.

  - ``nextstart``

    Called exactly **ONCE** when the **minimum period** for the `line iterator``
    has been met.

    The default behavior is to forward the call to ``next``, but can of course
    be overriden if needed.

Extra methods for *Indicators*
==============================

To speed up operations, `Indicators` support a batch operation mode which has
been termed as `runonce`. It is not strictly needed (a ``next`` method suffices)
but it greatly reduces time.

The `runonce` methods rules void the `get/set` point with index 0 and relies on
direct access to the underlying arrays holding the data and being passed the
right indices for each state.

The defined methods follow the naming of the next family:

  - ``once(self, start, end)``

    Called when the minimum period has been met. The internal array must be
    processed between start and end which are zero based from the start of the
    internal array

  - ``preonce(self, start, end)``

    Called before the minimum period has been met.

  - ``oncestart(self, start, end)``

    Called exactly **ONCE** when the minimum period has been met.

    The default behavior is to forward the call to ``once``, but can of course
    be overriden if needed.


Minimum Period
==============

A picture is worth a thousand words and in this case possibly an example
too. A SimpleMovingAverage is capable of explaining it::

  class SimpleMovingAverage(Indicator):
      lines = ('sma',)
      params = dict(period=20)

      def __init__(self):
          ...  # Not relevant for the explanation

      def prenext(self):
          print('prenext:: current period:', len(self))

      def nextstart(self):
          print('nextstart:: current period:', len(self))
	  # emulate default behavior ... call next
	  self.next()

      def next(self):
          print('next:: current period:', len(self))

And the instantiation could look like::

  sma = btind.SimpleMovingAverage(self.data, period=25)

Briefly explained:

  - Assuming the data passed to the moving average is a standard data feed its
    default period is ``1`` that is: the data feed produces a bar with no
    initial delay.

  - Then the **"period=25"** instantiated moving average would have its methods
    called as follows:

    - ``prenext`` 24 times
    - ``nextstart`` 1 time (in turn calling ``next``)
    - ``next`` n additional times until the *data feed* has been exhausted

Let's go for the killer indicator: *a SimpleMovingAverage* over another
*SimpleMovingAverage*. The instantiation could look like::

  sma1 = btind.SimpleMovingAverage(self.data, period=25)

  sma2 = btind.SimpleMovingAverage(sma1, period=20)

What now goes on:

  - The same as above for ``sma1``

  - ``sma2`` is receiving a **data feed** which has a *minimum period* of 25 which
    is our ``sma1`` and therefore

  - The ``sma2`` methods are called as indicated:

    - ``prenext`` the first 25 + 18 times for a total of 43 times

      - 25 times to let ``sma1`` produce its 1st sensible value

      - 18 times to accumulate extra ``sma1`` values

      - For a total of 19 values (1 after 25 calls and then 18 more)

    - ``nextstart`` then 1 time (in turn calling ``next``)
    - ``next`` the n additional times until the *data feed* has been exhausted

The platform is calling ``next`` when the system has already processed 44 bars.

The *minimum period* has been automatically adjusted to the incoming `data`.

Strategies and Indicators adhere to this behavior:

  - Only when the automatically calculated minimum period has been reached will
    ``next`` be called (barring the initial hook call to ``nextstart``)

.. note:: The same rules apply to ``preonce``, ``oncestart`` and ``once`` for
	  the **runonce** batch operation mode

.. note:: The **minimum period** behavior can be manipulated although it's not
	  recommended. Should it be wished used the ``setminperiod(minperiod)``
	  method in either Strategies or Indicators

Up and Running
**************

Getting up and running involves at least 3 *Lines* objects:

  - A Data feed
  - A Strategy (actually a class derived from Strategy)
  - A Cerebro (*brain* in Spanish)


Data Feeds
**********

These objects, obviously, provide the data which will be backtested by applying
calculations (direct and/or with Indicators)

The platform provides several data feeds:

  - Several CSV Format and a Generic CSV reader
  - Yahoo online fetcher
  - Support for receiving *Pandas DataFrames* and *blaze* objects
  - Live Data Feeds with *Interacive Brokers*, *Visual Chart* and *Oanda*

The platform makes no assumption about the content of the data feed such as
timeframe and compression. Those values, together with a name, can be supplied
for informational purposes and advance operations like Data Feed Resampling
(turning a for example a 5 minute Data Feed into a Daily Data Feed)

Example of setting up a Yahoo Finance Data Feed::

  import backtrader as bt
  import backtrader.feeds as btfeeds

  ...

  datapath = 'path/to/your/yahoo/data.csv'

  data = btfeeds.YahooFinanceCSVData(
      dataname=datapath,
      reversed=True)

The optional ``reversed`` parameter for Yahoo is shown, because the CSV files
directly downloaded from Yahoo start with the latest date, rather than with the
oldest.

If your data spans a large time range, the actual loaded data can be limited as follows::

  data = btfeeds.YahooFinanceCSVData(
      dataname=datapath,
      reversed=True
      fromdate=datetime.datetime(2014, 1, 1),
      todate=datetime.datetime(2014, 12, 31))

Both the *fromdate* and the *todate* will be included if present in the data
feed.

As already mentioned timeframe, compression and name can be added::

  data = btfeeds.YahooFinanceCSVData(
      dataname=datapath,
      reversed=True
      fromdate=datetime.datetime(2014, 1, 1),
      todate=datetime.datetime(2014, 12, 31)
      timeframe=bt.TimeFrame.Days,
      compression=1,
      name='Yahoo'
     )

If the data is plotted, those values will be used.


A Strategy (derived) class
**************************

.. note:: Before going on and for a more simplified approach, please check the
	  *Signals* section of the documentation if subclassing a strategy is
	  not wished.

The goal of anyone using the platform is backtesting the data and this is done
inside a Strategy (derived class).

There are 2 methods which at least need customization:

  - ``__init__``
  - ``next``

During initialization indicators on data and other calculations are created
prepared to later apply the logic.

The next method is later called to apply the logic for each and every bar of the
data.

.. note:: If data feeds of different timeframes (and thus different bar counts)
	  are passed the ``next`` method will be called for the master data
	  (the 1st one passed to cerebro, see below) which must be the the data
	  with the smaller timeframe

.. note:: If the Data Replay functionality is used, the ``next`` method will be
	  called several time for the same bar as the development of the bar is
	  replayed.

A basic Strategy derived class::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          self.sma = btind.SimpleMovingAverage(self.data, period=20)

      def next(self):

          if self.sma > self.data.close:
              self.buy()

          elif self.sma < self.data.close:
              self.sell()

Strategies have other methods (or hook points) which can be overriden::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          self.sma = btind.SimpleMovingAverage(self.data, period=20)

      def next(self):

          if self.sma > self.data.close:
              submitted_order = self.buy()

          elif self.sma < self.data.close:
              submitted_order = self.sell()

      def start(self):
          print('Backtesting is about to start')

      def stop(self):
          print('Backtesting is finished')

      def notify_order(self, order):
          print('An order new/changed/executed/canceled has been received')

The ``start`` and ``stop`` methods should be self-explanatory. As expected and
following the text in the print function, the ``notify_order`` method will be
called when the strategy needs a notification. Use case:

  - A buy or sell is requested (as seen in next)

    buy/sell will return an *order* which is submitted to the broker. Keeping a
    reference to this submitted order is up to the caller.

    It can for example be used to ensure that no new orders are submitted if an
    order is still pending.

  - If the order is Accepted/Executed/Canceled/Changed the broker will notify
    the status change (and for example execution size) back to the strategy via
    the notify method

The QuickStart guide has a complete and functional example of order management
in the ``notify_order`` method.

More can be done with other Strategy classes:

  - ``buy`` / ``sell`` / ``close``

    Use the underlying *broker* and *sizer* to send the broker a buy/sell
    order

    The same could be done by manually creating an Order and passing it over to
    the broker. But the platform is about making it easy for those using it.

    ``close`` will get the current market position and close it immediately.

  - ``getposition`` (or the property "position")

    Returns the current market position

  - ``setsizer``/``getsizer`` (or the property "sizer")

    These allow setting/getting the underlying stake Sizer. The same logic can
    be checked against Sizers which provide different stakes for the same
    situation (fixed size, proportional to capital, exponential)

    There is plenty of literature but Van K. Tharp has excellent books on the
    subject.

A Strategy is a *Lines* object and these support parameters, which are collected
using the standard Python kwargs argument::

  class MyStrategy(bt.Strategy):

      params = (('period', 20),)

      def __init__(self):

          self.sma = btind.SimpleMovingAverage(self.data, period=self.params.period)

      ...
      ...

Notice how the ``SimpleMovingAverage`` is no longer instantiated with a fixed
value of 20, but rather with the parameter "period" which has been defined for
the strategy.

A Cerebro
*********

Once Data Feeds are available and the Strategy has been defined, a Cerebro
instance is what brings everything together and execute the
actions. Instantiating one is easy::

  cerebro = bt.Cerebro()

Defaults are taking care of if nothing special is wished.

  - A default broker is created
  - No commission for the operations
  - Data Feeds will be preloaded
  - The default execution mode will be runonce (batch operation) which is the
    faster

    All indicators must support the ``runonce`` mode for full speed. The ones
    included in the platform do.

    Custom indicators do not need to implement the runonce
    functionality. ``Cerebro`` will simulate it, which means those non-runonce
    compatible indicators will run slower. But still most of the system will
    run in batch mode.

Since a Data feed is already available and a Strategy too (created earlier) the
standard way to put it all together and get it up and running is::

  cerebro.adddata(data)
  cerebro.addstrategy(MyStrategy, period=25)
  cerebro.run()

Notice the following:

  - The Data Feed "instance" is added

  - The MyStrategy "class" is added along with parameters (kwargs) that will be
    passed to it.

    The instantiation of MyStrategy will be done by cerebro in the background
    and any kwargs in "addstrategy" will be passed to it

The user may add as many Strategies and Data Feeds as wished. How Strategies
communicate with each other to achieve coordination (if wished be) is not
enforced/restricted by the platform.

Of course a Cerebro offers additional possibilities:

  - Decide about preloading and operation mode::

      cerebro = bt.Cerebro(runonce=True, preload=True)

    There is a constraint here: ``runonce`` needs preloading (if not, a batch
    operation cannot be run) Of course preloading Data Feeds does not enforce
    ``runonce``

  - ``setbroker`` / ``getbroker`` (and the *broker* property)

    A custom broker can be set if wished. The actual broker instance can also be
    accesed

  - Plotting. In a regular case as easy as::

      cerebro.run()
      cerebro.plot()

    plot takes some arguments for the customization

      - ``numfigs=1``

	If the plot is too dense it may be broken down into several plots

      - ``plotter=None``

	A customer plotter instance can be passed and cerebro will not
	instantiate a default one

      - ``**kwargs`` - standard keyword arguments

	Which will get passed to the plotter.

    Please see the plotting section for more information.

  - Optimization of strategies.

    As mentioned above, Cerebro gets a Strategy derived class (not an instance)
    and the keyword arguments that will be passed to it upon instantiation,
    which will happen when "run" is called.

    This is so to enable optimization. The same Strategy class will be
    instantiated as many times as needed with new parameters. If an instance had
    been passed to cerebro ... this would not be possible.

    Optimization is requested as follows::

      cerebro.optstrategy(MyStrategy, period=xrange(10, 20))

    The method ``optstrategy`` has the same signature as ``addstrategy`` but
    does extra housekeeping to ensure optimization runs as expected. A strategy
    could be expecting a *range* as a normal parameter for a strategy and
    ``addstrategy`` will make no assumptions about the passed parameter.

    On the other hand, ``optstrategy`` will understand that an iterable is a set
    of values that has to be passed in sequence to each instantiation of the
    Strategy class.

    Notice that instead of a single value a *range* of values is passed. In this
    simple case 10 values 10 -> 19 (20 is the upper limit) will be tried for
    this strategy.

    If a more complex strategy is developed with extra parameters they can all
    be passed to *optstrategy*. Parameters which must not undergo optimization
    can be passed directly without the end user having to create a dummy
    iterable of just one value. Example::

      cerebro.optstrategy(MyStrategy, period=xrange(10, 20), factor=3.5)

    The ``optstrategy`` method sees factor and creates (a needed) dummy iterable
    in the background for factor which has a single element (in the example 3.5)

    .. note:: Interactive Python shells and some types of frozen executables
       under *Windows* have problems with the Python ``multiprocessing`` module

       Please read the Python documentation about ``multiprocessing``.

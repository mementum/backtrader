Platform Concepts
#################

This is a collection of some of the concepts of the platform. It tries to gather
information bits which can be useful in using the platform.

Before Starting
***************

All mini-code examples assume the following imports are available::

  import backtrader as bt
  import backtrader.indicators as btind
  import backtrader.feeds as btfeeds

.. note::

   An alternative syntax for accessing sub-modules like *indicators* and *feeds*::

     import backtrader as bt

   And then::

     thefeed = bt.feeds.OneOfTheFeeds(...)
     theind = bt.indicators.SimpleMovingAverage(...)


Data Feeds - Passing them around
********************************

The basis of the work with the platform will be done with *Strategies*. And
these will get passed *Data Feeds*. The platform end user does not need to care
about receiving them:

  *Data Feeds are automagically provided member variables to the strategy in the
  form of an array and shortcuts to the array positions*

Quick preview of a Strategy derived class declaration and running the platform::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):

          sma = btind.SimpleMovingAverage(self.datas[0], period=self.params.period)

      ...

  cerebro = bt.Cerebro()

  ...

  data = btfeeds.MyFeed(...)
  cerebro.adddata(data)

  ...

  cerebro.addstrategy(MyStrategy, period=30)

  ...

Notice the following:

  - No ``*args`` or ``**kwargs`` are being received by the strategy's
    ``__init__`` method (they may still be used)
  - A member variable ``self.datas`` exists which is array/list/iterable holding
    at least one item (hopefully or else an exception will be raised)

So it is. *Data Feeds* get added to the platform and they will show up inside
the strategy in the sequential order in which they were added to the system.

.. note:: This also applies to ``Indicators``, should the end user develop his
	  own custom Indicator or when having a look at the source code for
	  some of the existing :ref:`indautoref`

Shortcuts for Data Feeds
========================

The `self.datas` array items can be directly accessed with additional automatic
member variables:

  - ``self.data`` targets ``self.datas[0]``
  - ``self.dataX`` targets ``self.datas[X]``

The example then::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):

          sma = btind.SimpleMovingAverage(self.data, period=self.params.period)

      ...

Omitting the Data Feeds
=======================

The example above can be further simplified to::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):

          sma = btind.SimpleMovingAverage(period=self.params.period)

      ...

``self.data`` has been completely removed from the invocation of
``SimpleMovingAverage``. If this is done, the indicator (in this case the
``SimpleMovingAverage``) receives the first data of the object in which is
being created (the *Strategy*), which is ``self.data`` (aka ``self.data0`` or
``self.datas[0]``)

Almost everything is a *Data Feed*
==================================

Not only `Data Feeds` are data and can be passed around. ``Indicators`` and
results of ``Operations`` are also data.

In the previous example the ``SimpleMovingAverage`` was receiving
``self.datas[0]`` as input to operate on. An example with operations and extra
indicators::

  class MyStrategy(bt.Strategy):
      params = dict(period1=20, period2=25, period3=10, period4)

      def __init__(self):

          sma1 = btind.SimpleMovingAverage(self.datas[0], period=self.p.period1)

	  # This 2nd Moving Average operates using sma1 as "data"
	  sma2 = btind.SimpleMovingAverage(sma1, period=self.p.period2)

	  # New data created via arithmetic operation
	  something = sma2 - sma1 + self.data.close

	  # This 3rd Moving Average operates using something  as "data"
	  sma3 = btind.SimpleMovingAverage(something, period=self.p.period3)

	  # Comparison operators work too ...
	  greater = sma3 > sma

	  # Pointless Moving Average of True/False values but valid
	  # This 4th Moving Average operates using greater  as "data"
	  sma3 = btind.SimpleMovingAverage(greater, period=self.p.period4)

      ...

Basically everything gets transformed into an object which can be used as a
data feed once it has been operated upon.

Parameters
**********

Mostly every other ``class`` in the platform supports the notion of
*parameters*.

  - Parameters along with default values are declared as a class attribute
    (tuple of tuples or dict-like object)
  - Keywords args (``**kwargs``) are scanned for matching parameters, removing
    them from ``**kwargs`` if found and assigning the value to the corresponding
    parameter
  - And parameters can be finally used in instances of the class by accessing
    the member variable ``self.params`` (shorthand: ``self.p``)

The previous quick Strategy preview already contains a parameters example, but
for the sake of redundancy, again, focusing only on the parameters. Using *tuples*::

  class MyStrategy(bt.Strategy):
      params = (('period', 20),)

      def __init__(self):
          sma = btind.SimpleMovingAverage(self.data, period=self.p.period)

And using a ``dict``::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):
          sma = btind.SimpleMovingAverage(self.data, period=self.p.period)


Lines
*****

Again mostly every other object in the platform is a ``Lines`` enabled
object. From a end user point of view this means:

  - It can hold one of more line series, being a line series an array of values
    were the values put together in a chart they would form a line.

A good example of a *line* (or *lineseries*) is the line formed by the closing
prices of a stock. This is actually a well-known chart representation of the
evolution of prices (known as *Line on Close*)

Regular use of the platform is only concerned with **accessing** ``lines``. The
previous mini-strategy example, lightly extended, comes in handy again::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):

          self.movav = btind.SimpleMovingAverage(self.data, period=self.p.period)

      def next(self):
          if self.movav.lines.sma[0] > self.data.lines.close[0]:
	      print('Simple Moving Average is greater than the closing price')

Two objects with ``lines`` have been exposed:

  - ``self.data``
    It has a ``lines`` attribute which contains a ``close`` attribute in turn
  - ``self.movav`` which is a ``SimpleMovingAverage`` indicator
    It has a ``lines`` attribute which contains a ``sma`` attribute in turn

.. note:: It should be obvious from this, that ``lines`` are named. They can
	  also be accessed sequentially following the declaration order, but
	  this should only be used in ``Indicator`` development

And both *lines*, namely ``close`` and ``sma`` can be queried for a point
(*index 0*) to compare the values.

Shorthand access to lines do exist:

  - ``xxx.lines`` can be shortened to ``xxx.l``
  - ``xxx.lines.name`` can be shortened to ``xxx.lines_name``
  - Complex objects like Strategies and Indicators offer quick access to data's
    lines

    - ``self.data_name`` offers a direct access to ``self.data.lines.name``
    - Which also applies to the numbered data variables: ``self.data1_name`` ->
      ``self.data1.lines.name``

Additionally the line names are directly accessible with:

  - ``self.data.close`` and ``self.movav.sma``

    But the notation doesn't make as clear as the previous one if *lines* are
    actually being accessed.

.. note:: **Setting**/**Assigning** the lines with these two later notations is
	  not supported

*Lines* declaration
===================

If an *Indicator* is being developed, the *lines* which the indicator has must
be declared.

Just as with *params* this takes place as a class attribute this time *ONLY* as
a tuple. Dictionaries are not supported because they do not store things
following insertion order.

For the Simple Moving Average it would be done like this::

  class SimpleMovingAverage(Indicator):
      lines = ('sma',)

      ...

.. note:: The *comma* following the declaration is needed in tuples if you pass
	  a single string to the tuple or else each letter in the string would be
	  interpreted as an item to be added to the tuple. Possibly one of the
	  few spots where Python's syntax got it wrong.

As seen in the previous example this declaration creates a ``sma`` line in the
*Indicator* that can be later accessed in the Strategy's logic (and possibly by
other indicators to create more complex indicators)

For development is sometimes useful to access the lines in a generic non-named
manner and this is where numbered access comes in handy:

  - ``self.lines[0]`` points to ``self.lines.sma``

Had more lines been defined they would be accessed with index 1, 2, and higher.

And of course, extra shorthand versions do exist:

  - ``self.line`` points to ``self.lines[0]``
  - ``self.lineX`` point to ``self.lines[X]``
  - ``self.line_X`` point to ``self.lines[X]``

Inside objects which are receiving *datas feeds* the lines below these data
feeds can also be quickly accessed by number:

  - ``self.dataY`` points to ``self.data.lines[Y]``
  - ``self.dataX_Y`` points to ``self.dataX.lines[X]`` which is a full shorthard
    version of ``self.datas[X].lines[Y]``

Accessing ``lines`` in *Data Feeds*
===================================

Inside *data feeds* the ``lines`` can also be accessed omitting the
``lines``. This makes it more natural to work with thinks like ``close``
prices.

For example::

  data = btfeeds.BacktraderCSVData(dataname='mydata.csv')

  ...

  class MyStrategy(bt.Strategy):

      ...

      def next(self):

          if self.data.close[0] > 30.0:
	      ...

Which seems more natural than the also valid: ``if self.data.lines.close[0] >
30.0:``. The same doesn't apply to ``Indicators`` with the reasoning being:

  - An ``Indicator`` could have an attribute ``close`` which holds an
    intermediate calculation, which is later delivered to the actual ``lines``
    also named ``close``

In the case of *Data Feeds*, no calculation takes place, because it is only a
data source.


*Lines* len
===========

*Lines* have a set of points and grow dynamically during execution, therefore
the length can be measured at any time by invoking the standard Python ``len``
function.

This applies to for example:

  - Data Feeds
  - Strategies
  - Indicators

An additional property applies to *Data Feeds* when the data is **preloaded**:

  - Method ``buflen``

The method returns the actual number of bars the *Data Feed* has available.

The difference between ``len`` and ``buflen``

  - ``len`` reports how many bars have been processed
  - ``buflen`` reports the total number of bars which have been loaded for the
    Data Feed

If both return the same value, either no data has been preloaded or the
processing of bars has consumed all preloaded bars (and unless the system is
connected to a live feed, this will mean the end of processing)

Inheritance of Lines and Params
===============================

A kind of metalanguage is in place to support declaration of *Params* and
*Lines*. Every effort has been made to make it compatible with standard Python
inheritance rules.

Params inheritance
------------------

Inheritance should work as expected:

  - Multiple inheritance is supported
  - Params from base classes are inherited
  - If multiple base classes define the same param the default value of the last
    class in the inheritance list is used
  - If the same param is redefined in a child class, the new default value takes
    over that of the base class

Lines Inheritance
-----------------

  - Multiple inheritance is supported
  - Lines from all base classes are inherited. Being *named* lines there will
    only be one version of a line if the same name has been used more than once
    in base classes

Indexing: 0 and -1
******************

*Lines* as seen before are line series and have a set of points that conform a
line when drawn together (like when joining all closing prices together along a
time axis)

To access those points in regular code, the choice has been to use a **0** based
approach for the current *get/set* instant.

Strategies do only *get* values. Indicators do also *set* values.

From the previous quick strategy example where the ``next`` method was briefly seen::

  def next(self):
      if self.movav.lines.sma[0] > self.data.lines.close[0]:
          print('Simple Moving Average is greater than the closing price')

The logic is *getting* the current value of the moving average and the current
closing price by applying index ``0``.

.. note:: Actually for index ``0`` and when applying logic/arithmetic operators
	  the comparison can be made directly as in::

	    if self.movav.lines.sma > self.data.lines.close:
	        ...

	  See later in the document the explanation for operators.

Setting is meant to be used when developing, for example, an `Indicator`,
because the current output value has to be `set` by the indicator.

A SimpleMovingAverage can be calculated for the current `get/set` point as
follows::

  def next(self):
    self.line[0] = math.fsum(self.data.get(0, size=self.p.period)) / self.p.period

Accessing previous `set` points has been modeled following the definition Python
makes for ``-1`` when accessing an array/iterable

  - It points to the last item of the array

The platform consider the last `set` item (before the current live `get/set`
point) to be ``-1``.

As such comparing the current ``close`` to the *previous* ``close`` is a ``0``
vs ``-1`` thing. In a strategy, for example::

  def next(self):
      if self.data.close[0] > self.data.close[-1]:
          print('Closing price is higher today')

Of course and logically, prices *set* before ``-1`` will be accessed with ``-2,
-3, ...``.

Slicing
*******

*backtrader* doesn't support slicing for *lines* objects and this is a design
decision following the ``[0]`` and ``[-1]`` indexing scheme. With regular
indexable Python objects you would do things like::

  myslice = self.my_sma[0:]  # slice from the beginning til the end

But remember that with the choice for ``0`` ... it is actually the currently
delivered value, there is nothing after it. Also::

  myslice = self.my_sma[0:-1]  # slice from the beginning til the end

Again ... ``0`` is the current value and ``-1`` is the latest (previous)
delivered value. That's why a slice from ``0`` -> ``-1`` makes no sense in the
*backtrader* ecosystem.

If slicing were ever to be supported, it would look like::

  myslice = self.my_sma[:0]  # slice from current point backwards to the beginning

or::

  myslice = self.my_sma[-1:0]  # last value and current value

or::

  myslice = self.my_sma[-3:-1]  # from last value backwards to the 3rd last value

Getting a slice
===============

An array with the latest values can still be gotten. The syntax::

  myslice = self.my_sma.get(ago=0, size=1)  # default values shown

That would have returned an arry with ``1`` value (``size=1``) with the current
moment ``0`` as the staring point to look backwards.

To get 10 values from the current point in time (i.e.: the last 10 values)::

  myslice = self.my_sma.get(size=10)  # ago defaults to 0

Of course the array has the ordering you would expect. The leftmost value is
the oldest one and the rightmost value is the most current (it is a regular
python array and not a *lines* object)

To get the last 10 values skipping only the current point::

  myslice = self.my_sma.get(ago=-1, size=10)


Lines: DELAYED indexing
***********************

The ``[]`` operator syntax is there to extract individual values during the
``next`` logic phase. *Lines* objects support an additional notation to address
values through a *delayed lines object* during the ``__init__`` phase.

Let's say that the interest in the logic is to compare the previous *close* value
to the actual value of a *simple moving average*. Rather than doing it manually
in each ``next`` iteration a pre-canned *lines* object can be generated::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):

          self.movav = btind.SimpleMovingAverage(self.data, period=self.p.period)
	  self.cmpval = self.data.close(-1) > self.sma

      def next(self):
          if self.cmpval[0]:
	      print('Previous close is higher than the moving average')

Here the ``(delay)`` notation is being used:

  - This delivers a replica of the ``close`` prices but delayed by ``-1``.

    And the comparison ``self.data.close(-1) > self.sma`` generates another
    *lines* object which returns either ``1`` if the condition is ``True`` or
    ``0`` if ``False``

Lines Coupling
**************

The operator ``()`` can be used as shown above with ``delay`` value to provide
a delayed version of a *lines* object.

If the syntax is used *WITHOUT* providing a ``delay`` value, then a
``LinesCoupler`` *lines* object is returned. This is meant to establish a
coupling between indicators that operate on *datas* with different timeframes.

Data Feeds with different timeframes have different *lengths*, and the
indicators operating on them replicate the length of the data. Example:

  - A daily data feed has around 250 bars per year

  - A weekly data feed has 52 bars per year

Trying to create an operation (for example) which compares 2 *simple moving
averages*, each operating on the datas quoted above would break. It would be
unclear how to match the 250 bars from the daily timeframe to the 52 bars of
the weekly timeframe.

The reader could imagine a ``date`` comparison taking place in the background
to find out a day - week correspondence, but:

  - ``Indicators`` are just mathematical formulas and have no *datetime*
    information

    They know nothing about the environment, just that if the data provides
    enough values, a calculation can take place.

The ``()`` (empty call) notation comes to the rescue::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):

          # data0 is a daily data
          sma0 = btind.SMA(self.data0, period=15)  # 15 days sma
	  # data1 is a weekly data
          sma1 = btind.SMA(self.data1, period=5)  # 5 weeks sma

	  self.buysig = sma0 > sma1()

      def next(self):
          if self.buysig[0]:
	      print('daily sma is greater than weekly sma1')

Here the larger timeframe indicator, ``sma1`` is *coupled* to the daily
timeframe with ``sma1()``. This returns an object which is compatible with the
larger numbers of bars of ``sma0`` and copies the values produced by ``sma1``,
effectively spreading the 52 weekly bars in 250 daily bars


Operators, using natural constructs
***********************************

In order to achieve the "ease of use" goal the platform allows (within the
constraints of Python) the use of operators. And to further enhance this goal
, the use of operators has been broken in two stages.

Stage 1 - Operators Create Objects
==================================

An example has already been seen even if not explicitly meant for this. During
the initialization phase (__init__ method) of objects like Indicators and
Strategies, operators create objects that can be operated upon, assigned or kept
as reference for later using during the evaluation phase of the Strategy's
logic.

Once again a potential implementation of a SimpleMovingAverage, further broken
down into steps.

The code inside the SimpleMovingAverage indicator `__init__` could look like::

  def __init__(self):
      # Sum N period values - datasum is now a *Lines* object
      # that when queried with the operator [] and index 0
      # returns the current sum

      datasum = btind.SumN(self.data, period=self.params.period)

      # datasum (being *Lines* object although single line) can be
      # naturally divided by an int/float as in this case. It could
      # actually be divided by anothr *Lines* object.
      # The operation returns an object assigned to "av" which again
      # returns the current average at the current instant in time
      # when queried with [0]

      av = datasum / self.params.period

      # The av *Lines* object can be naturally assigned to the named
      # line this indicator delivers. Other objects using this
      # indicator will have direct access to the calculation

      self.line.sma = av

A more complete use case is shown during the initialization of a Strategy::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          sma = btind.SimpleMovinAverage(self.data, period=20)

	  close_over_sma = self.data.close > sma
	  sma_dist_to_high = self.data.high - sma

	  sma_dist_small = sma_dist_to_high < 3.5

	  # Unfortunately "and" cannot be overridden in Python being
	  # a language construct and not an operator and thus a
	  # function has to be provided by the platform to emulate it

	  sell_sig = bt.And(close_over_sma, sma_dist_small)

After the above operations have taken place, *sell_sig* is a *Lines* object
which can be later used in the logic of the Strategy, indicating if the
conditions are met or not.

Stage 2 - Operators true to nature
==================================

Let's first remember that a strategy has a ``next`` method which is called for
every bar the system processes. This is where operators are actually in the
stage 2 mode. Building on the previous example::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          self.sma = sma = btind.SimpleMovinAverage(self.data, period=20)

	  close_over_sma = self.data.close > sma
	  self.sma_dist_to_high = self.data.high - sma

	  sma_dist_small = sma_dist_to_high < 3.5

	  # Unfortunately "and" cannot be overridden in Python being
	  # a language construct and not an operator and thus a
	  # function has to be provided by the platform to emulate it

	  self.sell_sig = bt.And(close_over_sma, sma_dist_small)

      def next(self):

          # Although this does not seem like an "operator" it actually is
	  # in the sense that the object is being tested for a True/False
	  # response

	  if self.sma > 30.0:
	      print('sma is greater than 30.0')

	  if self.sma > self.data.close:
	      print('sma is above the close price')

          if self.sell_sig:  # if sell_sig == True: would also be valid
	      print('sell sig is True')
	  else:
	      print('sell sig is False')

	  if self.sma_dist_to_high > 5.0:
	      print('distance from sma to hig is greater than 5.0')

Not a very useful strategy, just an example. During Stage 2 operators return the
expected values (boolean if testing for truth and floats if comparing them to
floats) and also arithmetic operations do.

.. note:: Notice that comparisons are actually not using the [] operator. This
	  is meant to further simplify things.

	  ``if self.sma > 30.0:`` ... compares ``self.sma[0]`` to ``30.0`` (1st
	  line and current value)

	  ``if self.sma > self.data.close:`` ... compares ``self.sma[0]`` to
	  ``self.data.close[0]``

Some non-overriden operators/functions
======================================

Python will not allow overriding everything and thus some functions are provided
to cope with the cases.

.. note:: Only meant to be used during Stage 1, to create objects which later
	  provide values.

Operators:

  - ``and`` -> ``And``
  - ``or`` -> ``Or``

Logic Control:

  - ``if`` -> ``If``

Functions:

  - ``any`` -> ``Any``
  - ``all`` -> ``All``
  - ``cmp`` -> ``Cmp``
  - ``max`` -> ``Max``
  - ``min`` -> ``Min``
  - ``sum`` -> ``Sum``

    ``Sum`` actually uses ``math.fsum`` as the underlying operation because the
    platform works with floating point numbers and applying a regular ``sum``
    may have an impact on precision.

  - ``reduce`` -> ``Reduce``

These utility operators/functions operate on iterables. The elements in the
iterables can be regular Python numeric types (ints, floats, ...) and also
objects with *Lines*.

An example generating a very dumb buy signal::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          sma1 = btind.SMA(self.data.close, period=15)
          self.buysig = bt.And(sma1 > self.data.close, sma1 > self.data.high)

      def next(self):
          if self.buysig[0]:
	      pass  # do something here

It is obvious that if the ``sma1`` is higher than the high, it must be higher
than the close. But the point is illustrating the use of ``bt.And``.

Using ``bt.If``::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          sma1 = btind.SMA(self.data.close, period=15)
          high_or_low = bt.If(sma1 > self.data.close, self.data.low, self.data.high)
	  sma2 = btind.SMA(high_or_low, period=15)

Breakdown:

  - Generate a ``SMA`` on ``data.close`` of ``period=15``

  - And then

    - ``bt.If`` the value of the *sma* is larger than ``close``, return
      ``low``, else return ``high``

      Remember that no actual value is being returned when ``bt.If`` is being
      invoked. It returns a *Lines* object which is just like a
      *SimpleMovingAverage*.

      The values will be calculated later when the system runs


  - The generated ``bt.If`` *Lines* object is then fed to a 2nd ``SMA`` which
    will sometimes use the ``low`` prices and sometimes the ``high`` prices for
    the calculation

Those **functions** take also numeric values. The same example with a modification::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          sma1 = btind.SMA(self.data.close, period=15)
          high_or_30 = bt.If(sma1 > self.data.close, 30.0, self.data.high)
	  sma2 = btind.SMA(high_or_low, period=15)

Now the 2nd moving average uses either ``30.0`` or the ``high`` prices to
perform the calculation, depending on the logic status of ``sma`` vs ``close``

.. note::
   The value ``30`` is transformed internally into a pseudo-iterable which
   always returns ``30``

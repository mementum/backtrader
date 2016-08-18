Using Indicators
################

Indicators can be used in two places in the platform:

  - Inside Strategies

  - Inside other Indicators

Indicators in action
********************

  #. Indicators are always instantiated during ``__init__`` in the *Strategy*

  #. Indicator values (or values thereof derived) are used/checked during
     ``next``

There is an important axiom to take into account:

  - Any ``Indicator`` (or value thereof derived) declared during ``__init__``
    will be precalculated before ``next`` is called.

Let's go for the differences an operation modes.

``__init__`` vs ``next``
************************

Things works as follows:

  - Any **operation** involving **lines** objects during ``__init__`` generates
    another **lines** object

  - Any **operation** involving **lines** objects during ``next`` yields regular
    Python types like floats and bools.


During ``__init__``
-------------------

Example of an operation during ``__init__``::

  hilo_diff = self.data.high - self.data.low

The variable ``hilo_diff`` holds a reference to a **lines** object which is
precalculated before calling ``next`` and can be accessed using the standard
array notation ``[]``

It does obviously contains for each bar of the data feed the difference between
the high and the low.

This also works when mixing simple **lines** (like those in the self.data Data
Feed) and complex ones like indicators::

  sma = bt.SimpleMovingAverage(self.data.close)
  close_sma_diff = self.data.close - sma

Now ``close_sma_diff`` contains again a **line** object.

Using logical operatorss::

  close_over_sma = self.data.close > sma

Now the generated **lines** object will contain an array of booleans.

During ``next``
---------------

Example of an operation (logical operator)::

  close_over_sma = self.data.close > self.sma

Using the equivalent array (index 0 based notation)::

  close_over_sma = self.data.close[0] > self.sma[0]

In this case ``close_over_sma`` yields a boolen which is the result of
comparing two floating point values, the ones returned by the ``[0]`` operator
applied to ``self.data.close`` and ``self.sma``

The ``__init__`` vs ``next`` *why*
----------------------------------

Logic simplification (and with it ease of use) is the key. Calculations and most
of the associated logic can be declared during ``__init__`` keeping the actual
operational logic to a minimum during ``next``.

There is actually a side benefit: **speed** (due to the precalculation explained
at the beginning)

A complete example which generates a **buy** signal during
``__init__``::

  class MyStrategy(bt.Strategy):

      def __init__(self):

          sma1 = btind.SimpleMovingAverage(self.data)
          ema1 = btind.ExponentialMovingAverage()

	  close_over_sma = self.data.close > sma1
	  close_over_ema = self.data.close > ema1
	  sma_ema_diff = sma - ema

	  buy_sig = bt.And(close_over_sma, close_over_ema, sma_ema_diff > 0)

      def next(self):

          if buy_sig:
              self.buy()

.. note:: Python's ``and`` operator cannot be overriden, forcing the platform to
	  define its own ``And``. The same applies to other constructs like
	  ``Or`` and ``If``

It should be obvious that the "declarative" approach during ``__init__`` keeps
the bloating of ``next`` (where the actual strategy work happens) to a minimum.

(Don't forget there is also a speed up factor)

.. note:: When the logic gets really complicated and involves several operations
	  it is usually much better to encapsulate that inside an
	  ``Indicator``.

Some notes
**********

In the example above there are two things which have been simplified in
``backtrader`` when compared to other platforms:

  - Declared ``Indicators`` are neither getting a **parent** parameter (like the
    strategy in which they are being created nor is any kind of "register"
    method/function being called.

    And in spite of it the strategy will kick the calculation of the
    ``Indicators`` and any **lines** object generated because of operations
    (like ``sma - ema``)

  - ``ExponentialMovingAverage`` is being instantiated without ``self.data``

    This is intentional. If no ``data`` is passed, the 1st data of the
    **parent** (in this case the Strategy in which is being created) will be
    automatically passed in the background


Indicator Plotting
******************

First and foremost:

  - Declared ``Indicators`` get automatically plotted (if cerebro.plot is
    called)

  - **lines** objects from operations DO NOT GET plotted (like ``close_over_sma
    = self.data.close > self.sma``)

    There is an auxiliary ``LinePlotterIndicator`` which plots such operations
    if wished with the following approach::

      close_over_sma = self.data.close > self.sma
      LinePlotterIndicator(close_over_sma, name='Close_over_SMA)

    The ``name`` parameter gives name to the **single** line held by this
    indicator.

Controlling plotting
--------------------

During the development of an ``Indicator`` a ``plotinfo`` declaration can be
added. It can be a tuple of tuples (2 elements), a ``dict`` or an
``OrderedDict``. It looks like::

  class MyIndicator(bt.Indicator):

      ....
      plotinfo = dict(subplot=False)
      ....

The value can be later accessed (and set) as follows (if needed)::

  myind = MyIndicator(self.data, someparam=value)
  myind.plotinfo.subplot = True

The value can even be set during instantiation::

  myind = MyIndicator(self.data, someparams=value, subplot=True)

The ``subplot=True`` will be passed to the (behind the scenes) intantiated
member variable ``plotinfo`` for the indicator.

The ``plotinfo`` offers the following parameters to control plotting behavior:

  - ``plot`` (default: ``True``)

    Whether the indicator is to be plotted or not

  - ``subplot`` (default: ``True``)

    Whether to plot the indicator in a different window. For indicators like
    moving averages the default is changed to ``False``

  - ``plotname`` (default: ``''``)

    Sets the plotname to show on the plot. The empty value means the canonical
    name of the indicator (``class.__name__``) will be used. This has some
    limitations because Python identifiers cannot use for example arithmetic
    operators.

    An indicator like DI+ will be declared as follows::

      class DIPlus(bt.Indicator):
          plotinfo=dict(plotname='DI+')

    Making the plot "nicer"

  - ``plotabove`` (default: ``False``)

    Indicators are usually plotted (those with ``subplot=True``) below the data
    they have operated on. Setting this to ``True`` will make the indicator be
    plotted above the data.

  - ``plotlinelabels`` (default: ``False``)

    Meant for "indicators" on "indicators". If one calculates the
    SimpleMovingAverage of the RSI the plot will usually show the name
    "SimpleMovingAverage" for the corresponding plotted line. This is the name
    of the "Indicator" and not the actual line being plotted.

    This default behavior makes sense because the user wants to usually see that
    a SimpleMovingAverage has been created using the RSI.

    if the value is set to ``True`` the actual name of the line inside the
    SimpleMovingAverage will be used.

  - ``plotymargin`` (default: ``0.0``)

    Amount of margin to leave at the top and bottom of the indicator (``0.15``
    -> 15%). Sometimes the ``matplotlib`` plots go too far to the top/bottom of
    the axis and a margin may be wished

  - ``plotyticks`` (default: ``[]``)

    Used to control the drawn y scale ticks

    If an empty list is passed the "y ticks" will be automatically
    calculated. For something like a Stochastic it may make sense to set this to
    well-known idustry standards like: ``[20.0, 50.0, 80.0]``

    Some indicators offer parameters like ``upperband`` and ``lowerband`` that
    are actually used to manipulate the y ticks

  - ``plothlines`` (default: ``[]``)

    Used to control the drawing of horizontal lines along the indicator axis.

    If an empty list is passed no horizontal lines will drawn.

    For something like a Stochastic it may make sense to draw lines for
    well-known idustry standards like: ``[20.0, 80.0]``

    Some indicators offer parameters like ``upperband`` and ``lowerband`` that
    are actually used to manipulate the horizontal lines

  - ``plotyhlines`` (default: ``[]``)

    Used to simultaneously control plotyticks and plothlines using a single parameter.

  - ``plotforce`` (default: ``False``)

    If for some reason you believe an indicator should be plotting and it is not
    plotting ... set this to ``True`` as a last resort.

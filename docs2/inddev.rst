Indicator Development
#####################

If anything (besides one or more winning Strategies) must ever be developed,
this something is a custom Indicator.

Such development within the platform is, according to the author, easy.

The following is needed:

  - A class derived from Indicator (either directly or from an already existing
    subclass)

  - Define the *lines* it will hold

    An indicator must at least have 1 line. If deriving from an existing one,
    the line(s) may have already be defined

  - Optionally define parameters which can alter the behavior

  - Optionally provided/customize some of the elements which enable sensible
    plotting of the indicators

  - Provide a fully defined operation in ``__init__`` with a binding
    (assignment) to the line(s) of the indicator or else provide ``next`` and
    (optionally) ``once`` methods

    If an indicator can be fully defined with logic/arithmetic operations during
    initialization and the result is assigned to the line: done

    Be it not the case, at least a ``next`` has to be provided where the indicator
    must assign a value to the line(s) at index 0

    Optimization of the calculation for the **runonce** mode (batch operation) can
    be achieved by providing a *once* method.

Important note: Idempotence
===========================

Indicators produce an output for each bar they receive. No assumption has to be
made about how many times the same bar will be sent. Operations have to be
idempotent.

The rationale behind this:

  - The same bar (index-wise) can be sent many times with changing values
    (namely the changing value is the closing price)

This enables, for example, "replaying" a daily session but using intraday data
which could be made of 5 minutes bars.

It could also allow the platform to get values from a live feed.

A dummy (but functional) indicator
**********************************

So can it be::

  class DummyInd(bt.Indicator):
      lines = ('dummyline',)

      params = (('value', 5),)

      def __init__(self):
          self.lines.dummyline = bt.Max(0.0, self.params.value)

Done! The indicator will output always the same value: either 0.0 or
self.params.value if it happens to be greater than 0.0.

The same indicator but using the next method::

  class DummyInd(bt.Indicator):
      lines = ('dummyline',)

      params = (('value', 5),)

      def next(self):
          self.lines.dummyline[0] = max(0.0, self.params.value)

Done! Same behavior.

.. note:: Notice how in the ``__init__`` version ``bt.Max`` is used to assign to
	  the Line object ``self.lines.dummyline``.

	  ``bt.Max`` returns an *lines* object that is automatically iterated for
	  each bar passed to the indicator.

	  Had ``max`` been used instead, the assigment would have been
	  pointless, because instead of a line, the indicator would have a
	  member variable with a fixed value.

	  During ``next`` the work is done directly with floating point values
	  and the standard ``max`` built-in can be used

Let's recall that ``self.lines.dummyline`` is the long notation and that it can
be shortened to:

  - ``self.l.dummyline``

and even to:

  - ``self.dummyline``

The latter being only possible if the code has not obscured this with a member
attribute.

The 3rd and last version provides an additional ``once`` method to optimize the
calculation::

  class DummyInd(bt.Indicator):
      lines = ('dummyline',)

      params = (('value', 5),)

      def next(self):
          self.lines.dummyline[0] = max(0.0, self.params.value)

      def once(self, start, end):
         dummy_array = self.lines.dummyline.array

	 for i in xrange(start, end):
	     dummy_array[i] = max(0.0, self.params.value)

A lot more effective but developing the ``once`` method has forced to scratch beyond
the surface. Actually the guts have been looked into.

The ``__init__`` version is in any case the best:

  - Everything is confined to the initialization

  - ``next`` and ``once`` (both optimized, because ``bt.Max`` already has them)
    are provided automatically with no need to play with indices and/or
    formulas

Be it needed for development, the indicator can also override the methods
associated to ``next`` and ``once``:

  - ``prenext`` and ``nexstart``
  - ``preonce`` and ``oncestart``


Manual/Automatic Minimum Period
*******************************

If possible the platform will calculate it, but manual action may be needed.

Here is a potential implementation of a *Simple Moving Average*::

  class SimpleMovingAverage1(Indicator):
      lines = ('sma',)
      params = (('period', 20),)

      def next(self):
          datasum = math.fsum(self.data.get(size=self.p.period))
          self.lines.sma[0] = datasum / self.p.period

Although it seems sound, the platform doesn't know what the minimum period is,
even if the parameter is named "period" (the name could be misleading and some
indicators receive several "period"s which have different usages)

In this case ``next`` would be called already for the 1st bar and everthing
would explode because get cannot return the needed ``self.p.period``.

Before solving the situation something has to be taken into account:

  - The `data feeds` passed to the indicators may already carry a **minimum
    period**

The sample *SimpleMovingAverage* may be done on for example:

  - A regular data feed

    This has a default mininum period of 1 (just wait for the 1st bar that
    enters the system)

  - Another Moving Average ... and this in turn already has a *period*

    If this is 20 and again our sample moving average has also 20, we end up
    with a minimum period of 40 bars

    Actually the internal calculation says 39 ... because as soon as the first
    moving average has produced a bar this counts for the next moving average,
    which creates an overlapping bar, thus 39 are needed.

  - Other indicators/objects which also carry periods

Alleviating the situation is done as follows::

  class SimpleMovingAverage1(Indicator):
      lines = ('sma',)
      params = (('period', 20),)

      def __init__(self):
          self.addminperiod(self.params.period)

      def next(self):
          datasum = math.fsum(self.data.get(size=self.p.period))
          self.lines.sma[0] = datasum / self.p.period

The ``addminperiod`` method is telling the system to take into account the extra
*period* bars needed by this indicator to whatever minimum period there may be
in existence.

Sometimes this is absolutely not needed, if all calculations are done with
objects which already communicate its period needs to the system.

A quick *MACD* implementation with Histogram::

    from backtrader.indicators import EMA

    class MACD(Indicator):
        lines = ('macd', 'signal', 'histo',)
        params = (('period_me1', 12), ('period_me2', 26), ('period_signal', 9),)

        def __init__(self):
            me1 = EMA(self.data, period=self.p.period_me1)
            me2 = EMA(self.data, period=self.p.period_me2)
            self.l.macd = me1 - me2
            self.l.signal = EMA(self.l.macd, period=self.p.period_signal)
	    self.l.histo = self.l.macd - self.l.signal

Done! No need to think about mininum periods.

  - ``EMA`` stands for *Exponential Moving Average* (a platform built-in alias)

    And this one (already in the platform) already states what it needs

  - The named lines of the indicator "macd" and "signal" are being assigned
    objects which already carry declared (behind the scenes) periods

      - `macd` takes the period from the operation "me1 - me2" which has in turn
	take the maximum from the periods of me1 and me2 (which are both
	exponential moving averages with different periods)

      - `signal` takes directly the period of the Exponential Moving Average over
	macd. This EMA also takes into account the already existing macd period
	and the needed amount of samples (period_signal) to calculate itself

      - `histo` takes the maximum of the two operands "signal - macd". Once both
	are ready can histo also produce a value

A full custom indicator
=======================

Let's develop a simple custom indicator which "indicates" if a moving average
(which can be modified with a parameter) is above the given data::

  import backtrader as bt
  import backtrader.indicators as btind

  class OverUnderMovAv(bt.Indicator):
      lines = ('overunder',)
      params = dict(period=20, movav=btind.MovAv.Simple)

      def __init__(self):
          movav = self.p.movav(self.data, period=self.p.period)
	  self.l.overunder = bt.Cmp(movav, self.data)

Done! The indicator will have a value of "1" if the average is above the data
and "-1" if below.

Be the data a regular data feed the 1s and -1s would be produced comparing with
the close price.

Although more can be seen in the *Plotting* section and to have a behaved and
nice citizen in the plotting world, a couple of things can be added::

  import backtrader as bt
  import backtrader.indicators as btind

  class OverUnderMovAv(bt.Indicator):
      lines = ('overunder',)
      params = dict(period=20, movav=bt.ind.MovAv.Simple)

      plotinfo = dict(
          # Add extra margins above and below the 1s and -1s
          plotymargin=0.15,

	  # Plot a reference horizontal line at 1.0 and -1.0
          plothlines=[1.0, -1.0],

	  # Simplify the y scale to 1.0 and -1.0
          plotyticks=[1.0, -1.0])

      # Plot the line "overunder" (the only one) with dash style
      # ls stands for linestyle and is directly passed to matplotlib
      plotlines = dict(overunder=dict(ls='--'))

      def _plotlabel(self):
          # This method returns a list of labels that will be displayed
	  # behind the name of the indicator on the plot

	  # The period must always be there
          plabels = [self.p.period]

	  # Put only the moving average if it's not the default one
          plabels += [self.p.movav] * self.p.notdefault('movav')

          return plabels

      def __init__(self):
          movav = self.p.movav(self.data, period=self.p.period)
	  self.l.overunder = bt.Cmp(movav, self.data)

.. _quickstart:

Quickstart
##########

Using the platform
******************

Let's run through a series of examples (from almost an empty one to a fully
fledged strategy) but not without before roughly explaining 2 basic concepts
when working with **backtrader**

  1. Lines

     Data Feeds, Indicators and Strategies have *lines*.

     A line is a succession of points that when joined together form this
     line. When talking about the markets, a Data Feed has usually the following
     set of points per day:

       - Open, High, Low, Close, Volume, OpenInterest

     The series of "Open"s along time is a Line. And therefore a Data Feed has
     usually 6 lines.

     If we also consider "DateTime" (which is the actual reference for a single
     point), we could count 7 lines.

  2. Index 0 Approach

     When accessing the values in a line, the current value is accessed with
     index: *0*

     And the "last" output value is accessed with *-1*. This in line with Python
     conventions for iterables (and a line can be iterated and is therefore an
     iterable) where index *-1* is used to access the "last" item of the
     iterable/array.

     In our case is the last **output** value what's getting accessed.

     As such and being index *0* right after *-1*, it is used to access the
     current moment in line.

With that in mind and if we imagine a Strategy featuring a Simple Moving
average created during initialization::

    self.sma = SimpleMovingAverage(.....)

The easiest and simplest way to access the current value of this moving average::

    av = self.sma[0]

There is no need to know how many bars/minutes/days/months have been processed,
because "0" uniquely identifies the current instant.

Following pythonic tradition, the "last" output value is accessed using *-1*::

    previous_value = self.sma[-1]

Of course earlier output values can be accessed with -2, -3, ...


From 0 to 100: the samples
**************************

Basic Setup
===========

Let's get running.

.. literalinclude:: ./quickstart01.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 10000.00
  Final Portfolio Value: 10000.00

In this example:

  - backtrader was imported

  - The Cerebro engine was instantiated

  - The resulting *cerebro* instance was told to *run* (loop over data)

  - And the resulting outcome was printed out

Although it doesn't seem much, let's point out something explicitly shown:

  - The Cerebro engine has created a *broker* instance in the background
  - The instance already has some cash to start with

This behind the scenes broker instantiation is a constant trait in the platform
to simplify the life of the user. If no broker is set by the user, a default one
is put in place.

And 10K monetary units is a usual value with some brokers to begin with.

Setting the Cash
================
In the world of finance, for sure only "losers" start with 10k. Let's change the
cash and run the example again.

.. literalinclude:: ./quickstart02.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 1000000.00
  Final Portfolio Value: 1000000.00

Mission accomplished. Let's move to tempestuous waters.

Adding a Data Feed
==================
Having cash is fun, but the purpose behind all this is to let an automated
strategy multiply the cash without moving a finger by operating on an asset
which we see as a *Data Feed*

Ergo ... No *Data Feed* -> **No Fun**. Let's add one to the ever growing
example.

.. literalinclude:: ./quickstart03.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 1000000.00
  Final Portfolio Value: 1000000.00

The amount of boilerplate has grown slightly, because we added:

  - Finding out where our example script is to be able to locate the sample
    *Data Feed* file

  - Having *datetime* objects to filter on which data from the *Data Feed* we
    will be operatign

Aside from that, the *Data Feed* is created and added to **cerebro**.

The output has not changed and it would be a miracle if it had.

.. note:: Yahoo Online sends the CSV data in date descending order, which is not
	  the standard convention. The *reversed=True* prameter takes into
          account that the CSV data in the file has already been **reversed**
          and has the standard expected date ascending order.

Our First Strategy
==================
The cash is in the *broker* and the *Data Feed* is there. It seems like risky
business is just around the corner.

Let's put a Strategy into the equation and print the "Close" price of each day
(bar).

**DataSeries** (the underlying class in *Data Feeds*) objects have aliases to
access the well known OHLC (Open High Low Close) daily values. This should ease
up the creation of our printing logic.

.. literalinclude:: ./quickstart04.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 100000.00
  2000-01-03T00:00:00, Close, 27.85
  2000-01-04T00:00:00, Close, 25.39
  2000-01-05T00:00:00, Close, 24.05
  ...
  ...
  ...
  2000-12-26T00:00:00, Close, 29.17
  2000-12-27T00:00:00, Close, 28.94
  2000-12-28T00:00:00, Close, 29.29
  2000-12-29T00:00:00, Close, 27.41
  Final Portfolio Value: 100000.00

Someone said the stockmarket was risky business, but it doesn't seem so.

Let's explain some of the magic:

  - Upon __init__ being called the strategy already has a list of datas that are
    present in the platform

    This is a standard Python *list* and datas can be accessed in the order they
    were inserted.

    The first data in the list `self.datas[0]` is the default data for trading
    operations and to keep all strategy elements synchronized (*it's the system
    clock*)

  - `self.dataclose = self.datas[0].close` keeps a reference to the *close
    line*. Only one level of indirection is later needed to access the close
    values.

  - The strategy `next` method will be called on each bar of the system clock
    (self.datas[0]). This is true until other things come into play like
    *indicators*, which need some bars to start producing an output. More on
    that later.


Adding some Logic to the Strategy
=================================
Let's try some crazy idea we had by looking at some charts

  - If the price has been falling 3 sessions in a row ... BUY BUY BUY!!!

.. literalinclude:: ./quickstart05.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 100000.00
  2000-01-03T00:00:00, Close, 27.85
  2000-01-04T00:00:00, Close, 25.39
  2000-01-05T00:00:00, Close, 24.05
  2000-01-05T00:00:00, BUY CREATE, 24.05
  2000-01-06T00:00:00, Close, 22.63
  2000-01-06T00:00:00, BUY CREATE, 22.63
  2000-01-07T00:00:00, Close, 24.37
  ...
  ...
  ...
  2000-12-20T00:00:00, BUY CREATE, 26.88
  2000-12-21T00:00:00, Close, 27.82
  2000-12-22T00:00:00, Close, 30.06
  2000-12-26T00:00:00, Close, 29.17
  2000-12-27T00:00:00, Close, 28.94
  2000-12-27T00:00:00, BUY CREATE, 28.94
  2000-12-28T00:00:00, Close, 29.29
  2000-12-29T00:00:00, Close, 27.41
  Final Portfolio Value: 95823.62

Several "BUY" creation orders were issued, our porftolio value was
decremented. A couple of important things are clearly missing.

  - The order was created but it is unknown if it was executed, when and at what
    price.

    The next example will build upon that by listening to notifications of order
    status.

The curious reader may ask how many shares are being bought, what asset is being
bought and how are orders being executed. Where possible (and in this case it is)
the platform fills in the gaps:

  - self.datas[0] (the main data aka system clock) is the target asset if no
    other one is specified
  - The stake is provided behind the scenes by a *position sizer* which uses a
    fixed stake, being the default "1". It will be modified in a later example
  - The order is executed "At Market". The broker (shown in previous examples)
    executes this using the opening price of the next bar, because that's the
    1st tick after the current under examination bar.
  - The order is executed so far without any commission (more on that later)


Do not only buy ... but SELL
============================

After knowing how to enter the market (long), an "exit concept" is needed and
also understanding whether the strategy is in the market.

  - Luckily a Strategy object offers access to a *position* attribute for the
    default *data feed*
  - Methods *buy* and *sell* return the **created** (not yet executed) order
  - Changes in orders' status will be notified to the strategy via a *notify*
    method

The *"exit concept"* will be an easy one:

  - Exit after 5 bars (on the 6th bar) have elapsed for good or for worse

    Please notice that there is no "time" or "timeframe" implied: number of
    bars. The bars can represent 1 minute, 1 hour, 1 day, 1 week or any other
    time period.

    Although we know the data source is a daily one, the strategy makes no
    assumption about that.

Additionally and to simplify:

  - Do only allow a Buy order if not yet in the market

.. note:: The *next* method gets no "bar index" passed and therefore it seems
          obscure how to understand when 5 bars may have elapsed, but this has
          been modeled in pythonic way: call *len* on an object and it will tell
          you the length of its *lines*. Just write down (save in a variable) at
          which length in an operation took place and see if the current length
          is 5 bars away.

.. literalinclude:: ./quickstart06.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 100000.00
  2000-01-03T00:00:00, Close, 27.85
  2000-01-04T00:00:00, Close, 25.39
  2000-01-05T00:00:00, Close, 24.05
  2000-01-05T00:00:00, BUY CREATE, 24.05
  2000-01-06T00:00:00, BUY EXECUTED, 23.61
  2000-01-06T00:00:00, Close, 22.63
  2000-01-07T00:00:00, Close, 24.37
  2000-01-10T00:00:00, Close, 27.29
  2000-01-11T00:00:00, Close, 26.49
  2000-01-12T00:00:00, Close, 24.90
  2000-01-13T00:00:00, Close, 24.77
  2000-01-13T00:00:00, SELL CREATE, 24.77
  2000-01-14T00:00:00, SELL EXECUTED, 25.70
  2000-01-14T00:00:00, Close, 25.18
  ...
  ...
  ...
  2000-12-15T00:00:00, SELL CREATE, 26.93
  2000-12-18T00:00:00, SELL EXECUTED, 28.29
  2000-12-18T00:00:00, Close, 30.18
  2000-12-19T00:00:00, Close, 28.88
  2000-12-20T00:00:00, Close, 26.88
  2000-12-20T00:00:00, BUY CREATE, 26.88
  2000-12-21T00:00:00, BUY EXECUTED, 26.23
  2000-12-21T00:00:00, Close, 27.82
  2000-12-22T00:00:00, Close, 30.06
  2000-12-26T00:00:00, Close, 29.17
  2000-12-27T00:00:00, Close, 28.94
  2000-12-28T00:00:00, Close, 29.29
  2000-12-29T00:00:00, Close, 27.41
  2000-12-29T00:00:00, SELL CREATE, 27.41
  Final Portfolio Value: 100018.53

Blistering Barnacles!!! The system made money ... something must be wrong


The broker says: Show me the money!
===================================

And the money is called "commission".

Let's add a reasonable *0.1%* commision rate per operation (both for buying and
selling ... yes the broker is avid ...)

A single line will suffice for it::

    cerebro.broker.setcommission(commission=0.001) # 0.1% ... divide by 100 to remove the %

Being experienced with the platform we want to see the profit or loss after a
buy/sell cycle, with and without commission.

.. literalinclude:: ./quickstart07.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 100000.00
  2000-01-03T00:00:00, Close, 27.85
  2000-01-04T00:00:00, Close, 25.39
  2000-01-05T00:00:00, Close, 24.05
  2000-01-05T00:00:00, BUY CREATE, 24.05
  2000-01-06T00:00:00, BUY EXECUTED, Price: 23.61, Cost: 23.61, Commission 0.02
  2000-01-06T00:00:00, Close, 22.63
  2000-01-07T00:00:00, Close, 24.37
  2000-01-10T00:00:00, Close, 27.29
  2000-01-11T00:00:00, Close, 26.49
  2000-01-12T00:00:00, Close, 24.90
  2000-01-13T00:00:00, Close, 24.77
  2000-01-13T00:00:00, SELL CREATE, 24.77
  2000-01-14T00:00:00, SELL EXECUTED, Price: 25.70, Cost: 25.70, Commission 0.03
  2000-01-14T00:00:00, OPERATION PROFIT, GROSS 2.09, NET 2.04
  2000-01-14T00:00:00, Close, 25.18
  ...
  ...
  ...
  2000-12-15T00:00:00, SELL CREATE, 26.93
  2000-12-18T00:00:00, SELL EXECUTED, Price: 28.29, Cost: 28.29, Commission 0.03
  2000-12-18T00:00:00, OPERATION PROFIT, GROSS -0.06, NET -0.12
  2000-12-18T00:00:00, Close, 30.18
  2000-12-19T00:00:00, Close, 28.88
  2000-12-20T00:00:00, Close, 26.88
  2000-12-20T00:00:00, BUY CREATE, 26.88
  2000-12-21T00:00:00, BUY EXECUTED, Price: 26.23, Cost: 26.23, Commission 0.03
  2000-12-21T00:00:00, Close, 27.82
  2000-12-22T00:00:00, Close, 30.06
  2000-12-26T00:00:00, Close, 29.17
  2000-12-27T00:00:00, Close, 28.94
  2000-12-28T00:00:00, Close, 29.29
  2000-12-29T00:00:00, Close, 27.41
  2000-12-29T00:00:00, SELL CREATE, 27.41
  Final Portfolio Value: 100016.98

God Save the Queen!!! The system still made money.

Before moving on, let's notice something by filtering the "OPERATION PROFIT"
lines::

  2000-01-14T00:00:00, OPERATION PROFIT, GROSS 2.09, NET 2.04
  2000-02-07T00:00:00, OPERATION PROFIT, GROSS 3.68, NET 3.63
  2000-02-28T00:00:00, OPERATION PROFIT, GROSS 4.48, NET 4.42
  2000-03-13T00:00:00, OPERATION PROFIT, GROSS 3.48, NET 3.41
  2000-03-22T00:00:00, OPERATION PROFIT, GROSS -0.41, NET -0.49
  2000-04-07T00:00:00, OPERATION PROFIT, GROSS 2.45, NET 2.37
  2000-04-20T00:00:00, OPERATION PROFIT, GROSS -1.95, NET -2.02
  2000-05-02T00:00:00, OPERATION PROFIT, GROSS 5.46, NET 5.39
  2000-05-11T00:00:00, OPERATION PROFIT, GROSS -3.74, NET -3.81
  2000-05-30T00:00:00, OPERATION PROFIT, GROSS -1.46, NET -1.53
  2000-07-05T00:00:00, OPERATION PROFIT, GROSS -1.62, NET -1.69
  2000-07-14T00:00:00, OPERATION PROFIT, GROSS 2.08, NET 2.01
  2000-07-28T00:00:00, OPERATION PROFIT, GROSS 0.14, NET 0.07
  2000-08-08T00:00:00, OPERATION PROFIT, GROSS 4.36, NET 4.29
  2000-08-21T00:00:00, OPERATION PROFIT, GROSS 1.03, NET 0.95
  2000-09-15T00:00:00, OPERATION PROFIT, GROSS -4.26, NET -4.34
  2000-09-27T00:00:00, OPERATION PROFIT, GROSS 1.29, NET 1.22
  2000-10-13T00:00:00, OPERATION PROFIT, GROSS -2.98, NET -3.04
  2000-10-26T00:00:00, OPERATION PROFIT, GROSS 3.01, NET 2.95
  2000-11-06T00:00:00, OPERATION PROFIT, GROSS -3.59, NET -3.65
  2000-11-16T00:00:00, OPERATION PROFIT, GROSS 1.28, NET 1.23
  2000-12-01T00:00:00, OPERATION PROFIT, GROSS 2.59, NET 2.54
  2000-12-18T00:00:00, OPERATION PROFIT, GROSS -0.06, NET -0.12

Adding up the "NET" profits the final figure is::

  15.83

But the system said the following at the end::

  2000-12-29T00:00:00, SELL CREATE, 27.41
  Final Portfolio Value: 100016.98

And obviously *15.83* is not *16.98*. There is no error whatsoever. The "NET"
profit of *15.83* is already cash in the bag.

Unfortunately (or fortunately to better understand the platform) there is an
open position on the last day of the *Data Feed*. Even if a SELL operation has
been sent ... IT HAS NOT YET BEEN EXECUTED.

The "Final Portfolio Value" calculated by the broker takes into account the
"Close" price on 2000-12-29. The actual execution price would have been set on
the next trading day which happened to be 2001-01-02. Extending the *Data Feed*"
to take into account this day the output is::

  2001-01-02T00:00:00, SELL EXECUTED, Price: 27.87, Cost: 27.87, Commission 0.03
  2001-01-02T00:00:00, OPERATION PROFIT, GROSS 1.64, NET 1.59
  2001-01-02T00:00:00, Close, 24.87
  2001-01-02T00:00:00, BUY CREATE, 24.87
  Final Portfolio Value: 100017.41

Now adding the previous NET profit to the completed operation's net profit::

  15.83 + 1.59 = 17.42

Which (discarding rounding errors in the "print" statements) is the extra
Portfolio above the initial 100000 monetary units the strategy started with.


Customizing the Strategy: Parameters
====================================

It would a bit unpractical to hardcode some of the values in the strategy and
have no chance to change them easily. *Parameters* come in handy to help.

Definition of parameters is easy and looks like::

  params = (('myparam', 27), ('exitbars', 5),)

Being this a standard Python tuple with some tuples inside it, the following may
look more appealling to some::

  params = (
      ('myparam', 27),
      ('exitbars', 5),
  )

With either formatting parametrization of the strategy is allowed when adding
the strategy to the Cerebro engine::

  # Add a strategy
  cerebro.addstrategy(TestStrategy, myparam=20, exitbars=7)


.. note:: The ``setsizing`` method below is deprecated. This content is kept
	  here for anyone looking at old samples of the sources. The sources
	  have been update to use::

	    cerebro.addsizer(bt.sizers.FixedSize, stake=10)``

	  Please read the section about *sizers*

Using the parameters in the strategy is easy, as they are stored in a "params"
attribute. If we for example want to set the stake fix, we can pass the stake
parameter to the *position sizer* like this durint __init__::

  # Set the sizer stake from the params
  self.sizer.setsizing(self.params.stake)

We could have also called *buy* and *sell* with a *stake* parameter and
*self.params.stake* as the value.

The logic to exit gets modified::

  # Already in the market ... we might sell
  if len(self) >= (self.bar_executed + self.params.exitbars):

With all this in mind the example evolves to look like:

.. literalinclude:: ./quickstart08.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 100000.00
  2000-01-03T00:00:00, Close, 27.85
  2000-01-04T00:00:00, Close, 25.39
  2000-01-05T00:00:00, Close, 24.05
  2000-01-05T00:00:00, BUY CREATE, 24.05
  2000-01-06T00:00:00, BUY EXECUTED, Size 10, Price: 23.61, Cost: 236.10, Commission 0.24
  2000-01-06T00:00:00, Close, 22.63
  ...
  ...
  ...
  2000-12-20T00:00:00, BUY CREATE, 26.88
  2000-12-21T00:00:00, BUY EXECUTED, Size 10, Price: 26.23, Cost: 262.30, Commission 0.26
  2000-12-21T00:00:00, Close, 27.82
  2000-12-22T00:00:00, Close, 30.06
  2000-12-26T00:00:00, Close, 29.17
  2000-12-27T00:00:00, Close, 28.94
  2000-12-28T00:00:00, Close, 29.29
  2000-12-29T00:00:00, Close, 27.41
  2000-12-29T00:00:00, SELL CREATE, 27.41
  Final Portfolio Value: 100169.80

In order to see the difference, the print outputs have also been extended to
show the execution size.

Having multiplied the stake by 10, the obvious has happened: the profit and loss
has been multiplied by 10. Instead of *16.98*, the surplus is now *169.80*


Adding an indicator
===================

Having heard of *indicators*, the next thing anyone would add to the strategy is
one of them. For sure they must be much better than a simple *"3 lower closes"*
strategy.

Inspired in one of the examples from PyAlgoTrade a strategy using a Simple
Moving Average.

  - Buy "AtMarket" if the close is greater than the Average
  - If in the market, sell if the close is smaller than the Average
  - Only 1 active operation is allowed in the market

Most of the existing code can be kept in place. Let's add the average during
__init__ and keep a reference to it::

  self.sma = bt.indicators.MovingAverageSimple(self.datas[0], period=self.params.maperiod)

And of course the logic to enter and exit the market will rely on the Average
values. Look in the code for the logic.

.. note:: The starting cash will be 1000 monetary units to be in line with the
          PyAlgoTrade example and no commission will be applied

.. literalinclude:: ./quickstart09.py
   :language: python
   :lines: 21-

Now, before skipping to the next section **LOOK CAREFULLY** to the first date
which is shown in the log:

  - It' no longer *2000-01-03*, the first trading day in the year 2K.

    It's 2000-01-24 ... *Who has stolen my cheese?*

The missing days are not missing. The platform has adapted to the new
circumstances:

  - An indicator (SimpleMovingAverage) has been added to the Strategy.

  - This indicator needs X bars to produce an output: in the example: 15

  - 2000-01-24 is the day in which the 15th bar occurs

The *backtrader* platform assumes that the Strategy has the indicator in place
for a good reason, **to use it in the decision making process**. And it makes no
sense to try to make decisions if the indicator is not yet ready and producing
values.

  - *next* will be 1st called when all indicators have already reached the
    minimum needed period to produce a value

  - In the example there is a single indicator, but the strategy could have any
    number of them.

After the execution the output is::

  Starting Portfolio Value: 1000.00
  2000-01-24T00:00:00, Close, 25.55
  2000-01-25T00:00:00, Close, 26.61
  2000-01-25T00:00:00, BUY CREATE, 26.61
  2000-01-26T00:00:00, BUY EXECUTED, Size 10, Price: 26.76, Cost: 267.60, Commission 0.00
  2000-01-26T00:00:00, Close, 25.96
  2000-01-27T00:00:00, Close, 24.43
  2000-01-27T00:00:00, SELL CREATE, 24.43
  2000-01-28T00:00:00, SELL EXECUTED, Size 10, Price: 24.28, Cost: 242.80, Commission 0.00
  2000-01-28T00:00:00, OPERATION PROFIT, GROSS -24.80, NET -24.80
  2000-01-28T00:00:00, Close, 22.34
  2000-01-31T00:00:00, Close, 23.55
  2000-02-01T00:00:00, Close, 25.46
  2000-02-02T00:00:00, Close, 25.61
  2000-02-02T00:00:00, BUY CREATE, 25.61
  2000-02-03T00:00:00, BUY EXECUTED, Size 10, Price: 26.11, Cost: 261.10, Commission 0.00
  ...
  ...
  ...
  2000-12-20T00:00:00, SELL CREATE, 26.88
  2000-12-21T00:00:00, SELL EXECUTED, Size 10, Price: 26.23, Cost: 262.30, Commission 0.00
  2000-12-21T00:00:00, OPERATION PROFIT, GROSS -20.60, NET -20.60
  2000-12-21T00:00:00, Close, 27.82
  2000-12-21T00:00:00, BUY CREATE, 27.82
  2000-12-22T00:00:00, BUY EXECUTED, Size 10, Price: 28.65, Cost: 286.50, Commission 0.00
  2000-12-22T00:00:00, Close, 30.06
  2000-12-26T00:00:00, Close, 29.17
  2000-12-27T00:00:00, Close, 28.94
  2000-12-28T00:00:00, Close, 29.29
  2000-12-29T00:00:00, Close, 27.41
  2000-12-29T00:00:00, SELL CREATE, 27.41
  Final Portfolio Value: 973.90

In the name of the King!!! A winning system turned into a losing one ... and
that with no commission. It may well be that **simply** adding an *indicator* is
not the universal panacea.

.. note:: The same logic and data with PyAlgoTrade yields a slightly different
	  result (slightly off). Looking at the entire printout reveals that
	  some operations are not exactly the same. Being the culprit again the
	  usual suspect: *rounding*.

	  PyAlgoTrade does not round the datafeed values when applying the
	  divided "adjusted close" to the data feed values.

	  The Yahoo Data Feed provided by *backtrader* rounds the values down
	  to 2 decimals after applying the adjusted close. Upon printing the
	  values everything seems the same, but it's obvious that sometimes
	  that 5th place decimal plays a role.

	  Rounding down to 2 decimals seems more realistic, because Marke
	  Exchanges do only allow a number of decimals per asset (being that 2
	  decimals usually for stocks)

.. note:: The Yahoo Data Feed (starting with version ``1.8.11.99`` allows to
	  specify if rounding has to happen and how many decimals)

Visual Inspection: Plotting
===========================

A printout or log of the actual whereabouts of the system at each bar-instant is
good but humans tend to be *visual* and therefore it seems right to offer a view
of the same whereabouts as chart.

.. note:: To plot you need to have *matplotlib* installed

Once again defaults for plotting are there to assist the platform user. Plotting
is incredibly a 1 line operation::

  cerebro.plot()

Being the location for sure after `cerebro.run()` has been called.

In order to display the automatic plotting capabilities and a couple of easy
customizations, the following will be done:

  - A 2nd MovingAverage (Exponential) will be added. The defaults will plot it
    (just like the 1st) with the data.
  - A 3rd MovingAverage (Weighted) will be added. Customized to plot in an own
    plot (even if not sensible)
  - A Stochastic (Slow) will be added. No change to the defaults.
  - A MACD will be added. No change to the defaults.
  - A RSI will be added. No change to the defaults.
  - A MovingAverage (Simple) will be applied to the RSI. No change to the
    defaults (it will be plotted with the RSI)
  - An AverageTrueRange will be added. Changed defaults to avoid it being
    plotted.

The entire set of additions to the __init__ method of the Strategy::

  # Indicators for the plotting show
  bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
  bt.indicators.WeightedMovingAverage(self.datas[0], period=25).subplot = True
  bt.indicators.StochasticSlow(self.datas[0])
  bt.indicators.MACDHisto(self.datas[0])
  rsi = bt.indicators.RSI(self.datas[0])
  bt.indicators.SmoothedMovingAverage(rsi, period=10)
  bt.indicators.ATR(self.datas[0]).plot = False

.. note:: Even if *indicators* are not explicitly added to a member variable of
	  the strategy (like self.sma = MovingAverageSimple...), they will
	  autoregister with the strategy and will influence the minimum period
	  for *next* and will be part of the plotting.

	  In the example only *RSI* is added to a temporary variable *rsi* with
	  the only intention to create a MovingAverageSmoothed on it.

The example now:

.. literalinclude:: ./quickstart10.py
   :language: python
   :lines: 21-

After the execution the output is::

  Starting Portfolio Value: 1000.00
  2000-02-18T00:00:00, Close, 27.61
  2000-02-22T00:00:00, Close, 27.97
  2000-02-22T00:00:00, BUY CREATE, 27.97
  2000-02-23T00:00:00, BUY EXECUTED, Size 10, Price: 28.38, Cost: 283.80, Commission 0.00
  2000-02-23T00:00:00, Close, 29.73
  ...
  ...
  ...
  2000-12-21T00:00:00, BUY CREATE, 27.82
  2000-12-22T00:00:00, BUY EXECUTED, Size 10, Price: 28.65, Cost: 286.50, Commission 0.00
  2000-12-22T00:00:00, Close, 30.06
  2000-12-26T00:00:00, Close, 29.17
  2000-12-27T00:00:00, Close, 28.94
  2000-12-28T00:00:00, Close, 29.29
  2000-12-29T00:00:00, Close, 27.41
  2000-12-29T00:00:00, SELL CREATE, 27.41
  Final Portfolio Value: 981.00

**The final result has changed even if the logic hasn't**. This is true but the
 logic has not been applied to the same number of bars.

.. note:: As explained before, the platform will first call next when all
	  indicators are ready to produce a value. In this plotting example
	  (very clear in the chart) the MACD is the last indicator to be fully
	  ready (all 3 lines producing an output). The 1st BUY order is no
	  longer scheduled during Jan 2000 but close to the end of Feb 2000.

The chart:

.. thumbnail:: ./quickstart10.png


Let's Optimize
==============

Many trading books say each market and each traded stock (or commodity or ..)
have different rythms. That there is no such thing as a one size fits all.

Before the plotting sample, when the strategy started using an indicator the
period default value was 15 bars. It's a strategy parameter and this can be used
in an optimization to change the value of the parameter and see which one better
fits the market.

.. note:: There is plenty of literature about Optimization and associated pros
	  and cons. But the advice will always point in the same direction: do
	  not overoptimize. If a trading idea is not sound, optimizing may end
	  producing a positive result which is only valid for the backtested
	  dataset.

The sample is modified to optimize the period of the Simple Moving Average. For
the sake of clarity any output with regards to Buy/Sell orders has been removed

The example now:

.. literalinclude:: ./quickstart11.py
   :language: python
   :lines: 21-

Instead of calling *addstrategy* to add a stratey class to Cerebro, the call is
made to *optstrategy*. And instead of passing a value a range of values is
passed.

One of the "Strategy" hooks is added, the *stop* method, which will be called
when the data has been exhausted and backtesting is over. It's used to print the
final net value of the portfolio in the broker (it was done in Cerebro
previously)

The system will execute the strategy for each value of the range. The following
will be output::

  2000-12-29, (MA Period 10) Ending Value 880.30
  2000-12-29, (MA Period 11) Ending Value 880.00
  2000-12-29, (MA Period 12) Ending Value 830.30
  2000-12-29, (MA Period 13) Ending Value 893.90
  2000-12-29, (MA Period 14) Ending Value 896.90
  2000-12-29, (MA Period 15) Ending Value 973.90
  2000-12-29, (MA Period 16) Ending Value 959.40
  2000-12-29, (MA Period 17) Ending Value 949.80
  2000-12-29, (MA Period 18) Ending Value 1011.90
  2000-12-29, (MA Period 19) Ending Value 1041.90
  2000-12-29, (MA Period 20) Ending Value 1078.00
  2000-12-29, (MA Period 21) Ending Value 1058.80
  2000-12-29, (MA Period 22) Ending Value 1061.50
  2000-12-29, (MA Period 23) Ending Value 1023.00
  2000-12-29, (MA Period 24) Ending Value 1020.10
  2000-12-29, (MA Period 25) Ending Value 1013.30
  2000-12-29, (MA Period 26) Ending Value 998.30
  2000-12-29, (MA Period 27) Ending Value 982.20
  2000-12-29, (MA Period 28) Ending Value 975.70
  2000-12-29, (MA Period 29) Ending Value 983.30
  2000-12-29, (MA Period 30) Ending Value 979.80

Results:

  * For periods below 18 the strategy (commissionless) loses money.
  * For periods between 18 and 26 (both included) the strategy makes money.
  * Above 26 money is lost agagin.

And the winning period for this strategy and the given data set is:

  * 20 bars, which wins 78.00 units over 1000 $/€ (a 7.8%)

.. note:: The extra indicators from the plotting example have been removed and
	  the start of operations is only influenced by the Simple Moving
	  Average which is being optimized. Hence the slightly different results
	  for period 15


Conclusion
==========

The incremental samples have shown how to go from a barebones script to a fully
working trading system which even plots the results and can be optimized.

A lot more can be done to try to improve the chances of winning:

  - Self defined Indicators

    Creating an indicator is easy (and even plotting them is easy)

  - Sizers

    Money Management is for many the key to success

  - Order Types (limit, stop, stoplimit)

  - Some others

To ensure all the above items can be fully utilized the documentation provides
an insight into them (and other topics)

Look in the table of contents and keep on reading ... and developing.

Best of luck

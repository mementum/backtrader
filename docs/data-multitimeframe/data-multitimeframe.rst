
Data - Multiple Timeframes
##########################

Sometimes investing decisions are taken using different timeframes:

  - Weekly to evaluate the trend

  - Daily to execute the entry

Or 5 minutes vs 60 minutes.

That implies that combining datas of multiple timeframes in ``backtrader`` is
needed to support such combinations.

Native support for it is already built-in. The end user must only follow these
rules:

  - The data with the smallest timeframe (and thus the larger number of bars)
    must be the 1st one to be added to the Cerebro instance

  - The datas must be properly date-time aligned for the platform to make any
    sense out of them

Beyond that, the end-user is free to apply indicators as wished on the
shorter/larger timeframes. Of course:

  - Indicators applied to larger timeframes will produce less bars

The platform will also have the following into account

  - The minimum period for larger timeframes

Minimum period which will probably have the side effect of having to consume
several orders of magnitude of the smaller timeframe bars before a Strategy
added to Cerebro kicks into action.

The built-in ``cerebro.resample`` is going to be used to create a larger timeframe.

Some examples below, but first the sauce of the test script.

.. literalinclude:: ./multitimeframe-example.py
   :language: python
   :lines: 68-89

The steps:

  - Load a data

  - Resample it according to the user specified arguments

    The script also allows for loading a 2nd data

  - Add the data to cerebro

  - Add the resampled data (larger timeframe) to cerebro

  - run

Example 1 - Daily and Weekly
============================

The invocation of the script::

  $ ./multitimeframe-example.py --timeframe weekly --compression 1

And the output chart:

.. thumbnail:: multitimeframe-daily-weekly.png


Example 2 - Daily and Daily Compression (2 bars to 1)
=====================================================

The invocation of the script::

  $ ./multitimeframe-example.py --timeframe daily --compression 2

And the output chart:

.. thumbnail:: multitimeframe-daily-daily-2.png


Example 3 - Strategy with SMA
=============================

Although plotting is nice, the key issue here is showing how the larger
timeframe influences the system, especially when it comes down to the starting
point

The script can take a ``--indicators`` to add a strategy which creates simple
moving averages of **period 10** on the smaller an larger timeframe datas.

If only the smaller timeframe was taken into account:

  - ``next`` would be called first after 10 bars, which is the time the Simple
    Moving Average needs to produce a value

    .. note::

       Remember that Strategy monitors created indicators and only calls
       ``next`` when all indicators have produced a value. The rationale is that
       the end user has added the indicators to use them in the logic and thus
       no logic should take place if the indicators have produced no values

But in this case the larger timeframe (weekly) delays the invocation of ``next``
until the Simple Moving Average oon the weekly data has produced a value, which
takes ... 10 weeks.

The script overrides ``nextstart`` which is only called once and which defaults
to calling ``next`` to show when it is first called.

Invocation 1:
-------------

Only the smaller timeframe, daily, gets a Simple Moving Average

The command line and output ::

  $ ./multitimeframe-example.py --timeframe weekly --compression 1 --indicators --onlydaily
  --------------------------------------------------
  nextstart called with len 10
  --------------------------------------------------

And the chart.

.. thumbnail:: multitimeframe-daily-weekly-indicators-onlydaily.png

Invocation 2:
-------------

Both timeframes get a Simple Moving Average

The command line::

  $ ./multitimeframe-example.py --timeframe weekly --compression 1 --indicators
  --------------------------------------------------
  nextstart called with len 50
  --------------------------------------------------
  --------------------------------------------------
  nextstart called with len 51
  --------------------------------------------------
  --------------------------------------------------
  nextstart called with len 52
  --------------------------------------------------
  --------------------------------------------------
  nextstart called with len 53
  --------------------------------------------------
  --------------------------------------------------
  nextstart called with len 54
  --------------------------------------------------

Two things to notice here:

  - Instead of being called after **10** periods, the strategy is 1st called
    after 50 periods.

    It is so because the Simple Moving Average applied on the larger (weekly)
    timeframe produces a value after 10 weeks ... and that is 10 weeks * 5 days
    / week ... 50 days

  - ``nextstart`` gets called 5 times rather than only 1.

    This is a natural side effect of having mixed the timeframe and having (in
    this case only one) indicators applied to the larger timeframe.

    The larger timeframe Simple Moving Average produces 5 times the same value
    whilst 5 daily bars are being consumed.

    And because the start of the period is being controlled by the larger
    timeframe ``nextstart`` gets called 5 times.

And the chart.

.. thumbnail:: multitimeframe-daily-weekly-indicators.png

Conclusion
==========

Multiple Timeframe Datas can be used in ``backtrader`` with no special objects
or tweaking: just add the smaller timeframes first.

The test script.

.. literalinclude:: ./multitimeframe-example.py
   :language: python
   :lines: 21-

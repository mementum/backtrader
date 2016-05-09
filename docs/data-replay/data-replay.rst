
Data - Replay
##########################

The time is gone and testing a strategy against a fully formed and closed bar is
good, but it could be better.

This is where *Data Replay* comes in to help. If:

  - The strategy operates on data with a timeframe X (example: daily)

and

  - Data for a smaller timeframe Y (example: 1 minute) is available

Data replay does exactly what the name implies::

  Replay a daily bar using the 1 minute data

This is of course not exactly how the market developed, but it is far better
than looking at the daily fully formed and closed bar in isolation::

  If the strategy operates in realtime during the formation of the daily bar,
  the approximation of the formation of the bar gives a chance to replicate the
  actual behavior of the strategy under real conditions

Putting *Data Replay* into action follows the regular usage patterns of
``backtrader``

  - Load a data feed

  - Pass the data to cerebro with ``replaydata``

  - Add a strategy

.. note::

   Preloading is not supported when data is being replayed because each bar
   is actually built in real-time. It will automatically disabled in any
   ``Cerebro`` instance.

Parameters which can be passed to ``replaydata``:

  - ``timeframe`` (default: bt.TimeFrame.Days)

    Destination timeframe  which to be useful has to
    be equal or larger than the source

  - ``compression`` (default: 1)

    Compress the selected value "n" to 1 bar

Extended parameters (do not touch if not really needed):

  - ``bar2edge`` (default: True)

    replays using time boundaries as the target of the closed bar. For
    example with a "ticks -> 5 seconds" the resulting 5 seconds bars will
    be aligned to xx:00, xx:05, xx:10 ...

  - ``adjbartime`` (default: False)

    Use the time at the boundary to adjust the time of the delivered
    resampled bar instead of the last seen timestamp. If resampling to "5
    seconds" the time of the bar will be adjusted for example to hh:mm:05
    even if the last seen timestamp was hh:mm:04.33

    .. note::

       Time will only be adjusted if "bar2edge" is True. It wouldn't make
       sense to adjust the time if the bar has not been aligned to a
       boundary

  - ``rightedge`` (default: True)

    Use the right edge of the time boundaries to set the time.

    If False and compressing to 5 seconds the time of a resampled bar for
    seconds between hh:mm:00 and hh:mm:04 will be hh:mm:00 (the starting
    boundary

    If True the used boundary for the time will be hh:mm:05 (the ending
    boundary)

For the sake of working with a example the standard 2006 daily data will be
replayed on a weekly basis. Which means:

  - There will finally be 52 bars, one for each week

  - Cerebro will call ``prenext`` and ``next`` a total of 255 times, which is
    the original count of daily bars

The trick:

  - When a weekly bar is forming, the length (``len(self)``) of the strategy
    will remain unchanged.

  - With each new week the length will increase by one

Some examples below, but first the sauce of the test script in which the data is
loaded and passed to cerebro with ``replaydata`` ... and then ``run``.

.. literalinclude:: ./replay-example.py
   :language: python
   :lines: 64-78


Example - Replay Daily to Weekly
================================

The invocation of the script::

  $ ./replay-example.py --timeframe weekly --compression 1

The chart cannot unfortunately show us the real thing happening in the
background, so let's have a look at the console output::

  prenext len 1 - counter 1
  prenext len 1 - counter 2
  prenext len 1 - counter 3
  prenext len 1 - counter 4
  prenext len 1 - counter 5
  prenext len 2 - counter 6
  ...
  ...
  prenext len 9 - counter 44
  prenext len 9 - counter 45
  ---next len 10 - counter 46
  ---next len 10 - counter 47
  ---next len 10 - counter 48
  ---next len 10 - counter 49
  ---next len 10 - counter 50
  ---next len 11 - counter 51
  ---next len 11 - counter 52
  ---next len 11 - counter 53
  ...
  ...
  ---next len 51 - counter 248
  ---next len 51 - counter 249
  ---next len 51 - counter 250
  ---next len 51 - counter 251
  ---next len 51 - counter 252
  ---next len 52 - counter 253
  ---next len 52 - counter 254
  ---next len 52 - counter 255

As we see the internal ``self.counter`` variable is keeping track of each call
to either ``prenext`` or ``next``. The former being called before the applied
Simple Moving Average produces a value. The latter called when the Simple Moving
Average is producing values.

The key:

  - The length (len(self)) of the strategy changes every 5 bars (5 trading days
    in the week)

The strategy is effectively seeing:

  - How the weekly bar developed in 5 shots.

    This, again, doesn't replicate the actual tick-by-tick (and not even minute,
    hour) development of the market, but it is better than actually seeing a
    bar.

The visual output is that of the weekly chart which is the final outcome the
system is being tested again.

.. thumbnail:: replay-daily-weekly.png


Example 2 - Daily to Daily with Compression
===========================================

Of course "Replaying" can be applied to the same timeframe but with a
compression.

The console::

  $ ./replay-example.py --timeframe daily --compression 2
  prenext len 1 - counter 1
  prenext len 1 - counter 2
  prenext len 2 - counter 3
  prenext len 2 - counter 4
  prenext len 3 - counter 5
  prenext len 3 - counter 6
  prenext len 4 - counter 7
  ...
  ...
  ---next len 125 - counter 250
  ---next len 126 - counter 251
  ---next len 126 - counter 252
  ---next len 127 - counter 253
  ---next len 127 - counter 254
  ---next len 128 - counter 255

This time we got half the bars as expected because of the factor 2 requested compression.

The chart:

.. thumbnail:: replay-daily-daily-compression-2.png

Conclusion
==========

A reconstruction of the market development is possible. Usually a smaller
timeframe set of data is available and can be used to discretely replay the
timeframe which the system operates on.

The test script.

.. literalinclude:: ./replay-example.py
   :language: python
   :lines: 21-

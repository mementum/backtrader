Advanced Operation
##################

Data - Multiple Timeframes
**************************

The platform supports operating on data feeds with different timeframes
simultaneously. In order to do so, two rules must be followed:

  - The data with the smallest timeframe (and thus the larger number of bars)
    must be the 1st one to be added to the Cerebro instance

  - The datas must be properly date-time aligned for the platform to make any
    sense out of them

Beyond that, the end-user is free to apply indicators as wished on the
shorter/larger timeframes. Of course:

  - Indicators applied to larger timeframes will produce less bars

The platform will also have the following into account

  - The minimum period for larger timeframes

Which will probably have the side effect of having to consume several orders of
magnitude of the smaller timeframe bars before a Strategy added to Cerebro kicks
into action.

Use case:

  - 1 day data bars for 1 year

    Around 256 bars

  - Weekly bars for the same data set

    52 bars

With the exception of the "smallest timeframe first" rule, there is nothing
special to do::

  cerebro = bt.Cerebro(runonce=True, preload=True)

  data_daily = bt.feeds.YahooFinanceCSVData(
      dataname=datapath,
      fromdate=datetime.datetime(2014, 1, 1),
      todate=datetime.datetime(2014, 12, 31),
      compression=1,
      timeframe=bt.TimeFrame.Days)

  # SMALLEST TIMEFRAME FIRST
  cerebro.adddata(data_daily)

  data_weekly = bt.feeds.YahooFinanceCSVData(
      dataname=datapath,
      fromdate=datetime.datetime(2014, 1, 1),
      todate=datetime.datetime(2014, 12, 31),
      compression=1,
      timeframe=bt.TimeFrame.Weeks)

  cerebro.adddata(data_weekly)

  ...

  cerebro.run()

Bear in mind:

  - In the strategy ``self.data0`` (or ``self.data``) will refer to the 1st
    added data which in this case is the daily

  - ``self.data1`` will refer to the weekly data

A quick Strategy snippet::

  class MyStrategy(bt.Strategy):
      params = dict(period=20)

      def __init__(self):

          ma_day = btind.SimpleMovingAverage(self.data0, period=self.p.period)
	  ma_week = btind.SimpleMovingAverage(self.data1, period=self.p.period)

      def next(self):
          print('Called first after so many data0 bars:', len(self))

In a single data scenario and with the default `20` for period ``next`` would be
called after 20 iterations.

But in this case with daily and weekly data ``next`` will be called after 20
weekly bars have elapsed, which amounts in a regular case to about `90 daily`
bars.

  - The strategy kicks first in action after 90 data bars because of the weekly
    timeframe effect


Data - Resampling
*****************

Data can be resampled to a larger timeframe:

  - Minutes to Minutes (for example 5 to 60)
  - Minutes to Days, Weeks, Months, Years
  - Days to Weeks, Months, Years
  - Weeks to Months, Years
  - Months to Years

To do it, the data feed is passed to a *DataResampler*, which is what finally
gets added to the Cerebro instance. An non-resample example::

  cerebro = bt.Cerebro(runonce=True, preload=True)

  data = bt.feeds.YahooFinanceCSVData(
      dataname=datapath,
      fromdate=datetime.datetime(2014, 1, 1),
      todate=datetime.datetime(2014, 6, 30),
      compression=5,
      timeframe=bt.TimeFrame.Minutes)

  cerebro.adddata(data)

  ...

  cerebro.run()

For a regular data feed like the one above the "compression" and "timeframe"
keyword arguments are just hints (they also make nicer plotting)

The same keyword arguments for a *DataResampler* are the key to decide what to
resample to. A resampled example::

  cerebro = bt.Cerebro(runonce=True, preload=True)

  data = bt.feeds.YahooFinanceCSVData(
      dataname=datapath,
      fromdate=datetime.datetime(2014, 1, 1),
      todate=datetime.datetime(2014, 6, 30),
      compression=5,
      timeframe=bt.TimeFrame.Minutes)

  data_resampled = bt.DataResampler(data=data,
      timeframe=bt.TimeFrame.Days,
      compression=2)

  cerebro.adddata(data_resampled)

  ...

  cerebro.run()

Done! Instead of adding "data" directly to the cerebro, it is fed to a
DataResampler.

  - The original data is in Minutes and each bar represents 5 minutes

    Remember only hints

  - The Resampler will work to deliver:

      * Days
      * 2 days per bar

Of course resampling will only output the requested timeframe if the original
data makes sense. Passing weekly bars and requesting daily bars will not work.


Data - Replay
*************

Replaying adds an extra bit to resampling:

  - The resampled bar will be output as many times as needed to the system
    during the resampling process

The indicators and strategies will see its next operations called as
many times as the bar is output.

This allows to experience how, for example, a day has happened and may play a
role in some strategies and indicators which may make decisions based on the
development of a daily bar (for example: status of a MACD indicator 5 minutes
before the close of a session)

It is obvious that *next* methods in indicators must store no state in between
calls.

.. note:: Replaying data only works in step by step mode, which means the
	  runconce (bath operation) mode is not available.

	  In the ``next`` method of an indicator the current number of bars of the
	  system can be checked (with len(self)) and during replay this value
	  may not change for a long streak of bars.

	  Hence something like *self.line[0] = result_of_indicator_operation*
	  will output a result for the same bar several times. Which is the
	  expected thing to see the development of an indicator in real-time
	  whilst for example a daily bar is being replayed.

	  Obviously "preloading" has to also be set to False

Just like with resampling, the data has to be passed to a DataReplayer which is
what finally gets added to cerebro::

  # Notice "runconce=False" for replaying
  cerebro = bt.Cerebro(runonce=False, preload=False)

  data = bt.feeds.YahooFinanceCSVData(
      dataname=datapath,
      fromdate=datetime.datetime(2014, 1, 1),
      todate=datetime.datetime(2014, 6, 30),
      compression=5,
      timeframe=bt.TimeFrame.Minutes)

  data_replayed = bt.DataReplayer(data=data,
      timeframe=bt.TimeFrame.Days,
      compression=2)

  cerebro.adddata(data_replayed)

  ...

  cerebro.run()

Same syntax, just a different object.

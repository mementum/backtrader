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

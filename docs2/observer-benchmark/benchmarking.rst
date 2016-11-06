
Benchmarking
############

`Ticket #89 <https://github.com/mementum/backtrader/issues/89>`_ is about
adding benchmarking against an asset. Sensible as one may actually have a
strategy that even if positive is below what simply tracking the asset would
have delivered.

*backtrader* includes 2 different types of objects which can aid with tracking:

  - *Observers*
  - *Analyzers*

In the realm of *Analyzers* there was already a ``TimeReturn`` object which
tracks the evolution of the returns of the entire portfolio value (i.e:
including cash)

This could have also obviously been an *Observer*, so whilst adding some
*benchmarking* some work has also gone into being able to plug together an
*Observer* and an *Analyzer* which are meant to track the same thing.

.. note::

   The major difference between *Observers* and *Analyzers* is the *lines*
   nature of *observers*, which record every value and this makes them suitable
   for plotting and real time querying. This of course consumes memory.

   *Analyzers* on the other hand return a set of results via ``get_analysis``
   and the implementation may not deliver any result until the very end of a
   *run*.

Analyzers - Benchmarking
************************

The standard ``TimeReturn`` analyzer has been extended to support tracking a
*data feed*. The 2 major parameters invoved:

   - ``timeframe`` (default: ``None``)
     If ``None`` then the complete return over the entire backtested period
     will be reported

     Pass ``TimeFrame.NoTimeFrame`` to consider the entire dataset with no
     time constraints

   - ``data`` (default: ``None``)

     Reference asset to track instead of the portfolio value.

     .. note:: this data must have been added to a ``cerebro`` instance with
               ``addata``, ``resampledata`` or ``replaydata``

For more details and parameters: :doc:`../analyzers-reference`

As such, the returns of the porftolio on a yearly basis can be tracked like
this

.. code-block:: python

  import backtrader as bt

  cerebro = bt.Cerebro()
  cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years)

  ...  # add datas, strategies ...

  results = cerebro.run()
  strat0 = results[0]

  # If no name has been specified, the name is the class name lowercased
  tret_analyzer = strat0.analyzers.getbyname('timereturn')
  print(tret_analyzer.get_analysis())


If we wanted to track the returns of a *data*

.. code-block:: python

  import backtrader as bt

  cerebro = bt.Cerebro()

  data = bt.feeds.OneOfTheFeeds(dataname='abcde', ...)
  cerebro.adddata(data)

  cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years,
                      data=data)

  ...  # add strategies ...

  results = cerebro.run()
  strat0 = results[0]

  # If no name has been specified, the name is the class name lowercased
  tret_analyzer = strat0.analyzers.getbyname('timereturn')
  print(tret_analyzer.get_analysis())

If both are to be tracked, the best is to assign names to the *analyzers*

.. code-block:: python

  import backtrader as bt

  cerebro = bt.Cerebro()

  data = bt.feeds.OneOfTheFeeds(dataname='abcde', ...)
  cerebro.adddata(data)

  cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years,
                      data=data, _name='datareturns')

  cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years)
                      _name='timereturns')

  ...  # add strategies ...

  results = cerebro.run()
  strat0 = results[0]

  # If no name has been specified, the name is the class name lowercased
  tret_analyzer = strat0.analyzers.getbyname('timereturns')
  print(tret_analyzer.get_analysis())
  tdata_analyzer = strat0.analyzers.getbyname('datareturns')
  print(tdata_analyzer.get_analysis())


Observers - Benchmarking
************************

Thanks to the background machinery allowing the usage of *Analyzers* inside
*Observers*, 2 new observers have been added:

  - ``TimeReturn``
  - ``Benchmark``

Both use the ``bt.analyzers.TimeReturn`` analyzer to collect results.

Rather than having code snippets like above, a full sample with some runs to
show their functionality.

Observing TimeReturn
--------------------

Execution::

  $ ./observer-benchmark.py --plot --timereturn --timeframe notimeframe

.. thumbnail:: 01-benchmarking-timereturn-no-timeframe.png

Notice the execution options:

  - ``--timereturn`` telling the sample to do just that

  - ``--timeframe notimeframe`` telling the analyzer to consider the entire
    data set disregarding timeframe boundaries.

The last plotted value is ``-0.26``.

  - The starting cash (obvious from the chart) are ``50K`` monetary units and the strategy ends
    up with ``36,970`` monetary units and hence a ``-26%`` value decrement.

Observing Benchmarking
----------------------

Because *benchmarking* will also display the *timereturn* results, let's run
the same thing but with *benchmarking* active::

  $ ./observer-benchmark.py --plot --timeframe notimeframe

.. thumbnail:: 02-benchmarking-no-timeframe.png

Hey, hey hey!!!

  - The strategy is better than the asset: ``-0.26`` vs ``-0.33``

    It shouldn't be a matter for celebration but at least is clear the strategy
    is not even as bad as the asset.

Moving down to track things on a *yearly* basis::

  $ ./observer-benchmark.py --plot --timeframe years

.. thumbnail:: 03-benchmarking-years.png

Watch out!

  - The strategy last value has changed very slightly from ``-0.26`` to
    ``-0.27``

  - The asset on the on the other hand shows a last value of ``-0.35`` (versus
    ``-0.33`` above)

The reason for values so close to each other is that when moving from 2005 to
2006, both the strategy and the benchmarking asset were almost at the starting
level from the beginning of 2005.

Switching to a lower timeframe like *weeks*, the entire picture changes::

  $ ./observer-benchmark.py --plot --timeframe weeks

  .. thumbnail:: 04-benchmarking-weeks.png

Now:

  - The ``Benchmark`` observer shows a much more nervous aspect. Things move up
    and down, because now ``weekly`` returns for both the portfolio and the
    data are being tracked

  - And because no trade was active in the last week of the year and the asset
    barely moved, the last displayed values are 0.00 (The last closing value
    before the last week was ``25.54`` and the sample data closed at ``25.55``,
    and the difference is felt first at the 4th decimal point)

Observing Benchmarking - Another data
-------------------------------------

The sample allows to benchmark against a different data. The default is to
benchmark against *Oracle* when using ``--benchdata1``. Considering the entire
dataset with ``--timeframe notimeframe``::

  $ ./observer-benchmark.py --plot --timeframe notimeframe --benchdata1

.. thumbnail:: 05-benchmarking-data1-no-timeframe.png

It's clear now why there was no reason for celebration above:

  - The results of the strategy have not changed for ``notimeframe`` and remain
    at ``-26%`` (``-0.26``)

  - But when benchmarking against another data, this data has a ``+23%``
    (``0.23`` ) in the same period

Either the strategy needs a change or another asset better be traded.


Concluding
**********

There are now two ways, using the same underlying code/calculations, to track
the *TimeReturn* and *Benchmark*

  - *Observers*  (``TimeReturn`` and ``Benchmark``)

and

  - *Analyzer* (``TimeReturn`` and ``TimeReturn`` with a ``data`` parameter)

Of course *benchmarking* doesn't guarantee profit, just *comparison*.

Usage of the sample::

  $ ./observer-benchmark.py --help
  usage: observer-benchmark.py [-h] [--data0 DATA0] [--data1 DATA1]
                               [--benchdata1] [--fromdate FROMDATE]
                               [--todate TODATE] [--printout] [--cash CASH]
                               [--period PERIOD] [--stake STAKE] [--timereturn]
                               [--timeframe {months,days,notimeframe,years,None,weeks}]
                               [--plot [kwargs]]

  Benchmark/TimeReturn Observers Sample

  optional arguments:
    -h, --help            show this help message and exit
    --data0 DATA0         Data0 to be read in (default:
                          ../../datas/yhoo-1996-2015.txt)
    --data1 DATA1         Data1 to be read in (default:
                          ../../datas/orcl-1995-2014.txt)
    --benchdata1          Benchmark against data1 (default: False)
    --fromdate FROMDATE   Starting date in YYYY-MM-DD format (default:
                          2005-01-01)
    --todate TODATE       Ending date in YYYY-MM-DD format (default: 2006-12-31)
    --printout            Print data lines (default: False)
    --cash CASH           Cash to start with (default: 50000)
    --period PERIOD       Period for the crossover moving average (default: 30)
    --stake STAKE         Stake to apply for the buy operations (default: 1000)
    --timereturn          Use TimeReturn observer instead of Benchmark (default:
                          None)
    --timeframe {months,days,notimeframe,years,None,weeks}
                          TimeFrame to apply to the Observer (default: None)
    --plot [kwargs], -p [kwargs]
                          Plot the read data applying any kwargs passed For
                          example: --plot style="candle" (to plot candles)
                          (default: None)


The code
--------

.. literalinclude:: ./observer-benchmark.py
   :language: python
   :lines: 21-

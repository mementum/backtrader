
Automating BackTesting
######################

So far all ``backtrader`` examples and working samples have started from scratch
creating a main **Python** module which loads datas, strategies, observers and
prepares cash and commission schemes.

One of the goals of *algorithmic trading* is the automation of trading and given
that bactrader is a *backtesting* platform intented to check trading algorithms
(hence is an *algotrading* platform), automating the use of backtrader was an
obvious goal.

``backtrader`` contains the ``bt-run.py`` script which automates most tasks and
will be installed along ``backtrader`` as part of a regular package.

``bt-run.py`` allows the end user to:

  - Say which datas have to be loaded
  - Set the format to load the datas
  - Specify the date range for the datas
  - Disable standard observers
  - Load one or more observers (example: DrawDown) from the built-in ones or
    from a python module
  - Set the cash and commission scheme parameters for the broker (commission,
    margin, mult)
  - Enable plotting, controlling the amount of charts and style to present the
    data

And finally:

  - Load a strategy (a built-in one or from a Python module)
  - Pass parameters to the loaded strategy

See below for the **Usage*** of the script.

Applying a User Defined Strategy
================================

Let's consider the following strategy which:

  - Simply loads a SimpleMovingAverage (default period 15)
  - Prints outs
  - Is in a fily with the name mymod.py

.. literalinclude:: ./mymod.py
   :language: python
   :lines: 21-

Executing the strategy with the usual testing sample is easy:
easy::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2006-day-001.txt \
              --strategy ./mymod.py

The chart output

.. thumbnail:: ./bt-run-mymod-no-params.png

The console output::

  2006-01-20T23:59:59+00:00, 15, 3593.16, 3612.37, 3550.80, 3550.80, 0.00, 0.00
  2006-01-23T23:59:59+00:00, 16, 3550.24, 3550.24, 3515.07, 3544.31, 0.00, 0.00
  2006-01-24T23:59:59+00:00, 17, 3544.78, 3553.16, 3526.37, 3532.68, 0.00, 0.00
  2006-01-25T23:59:59+00:00, 18, 3532.72, 3578.00, 3532.72, 3578.00, 0.00, 0.00
  ...
  ...
  2006-12-22T23:59:59+00:00, 252, 4109.86, 4109.86, 4072.62, 4073.50, 0.00, 0.00
  2006-12-27T23:59:59+00:00, 253, 4079.70, 4134.86, 4079.70, 4134.86, 0.00, 0.00
  2006-12-28T23:59:59+00:00, 254, 4137.44, 4142.06, 4125.14, 4130.66, 0.00, 0.00
  2006-12-29T23:59:59+00:00, 255, 4130.12, 4142.01, 4119.94, 4119.94, 0.00, 0.00

Same strategy but:

  - Setting the parameter ``period`` to 50

The command line::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2006-day-001.txt \
	      --plot \
              --strategy ./mymod.py:period=50

The chart output.

.. thumbnail:: ./bt-run-mymod-period-50.png

.. note::
   if no ``.py`` extension is given, bt-run will add it.

Using a built-in Strategy
=========================

``backtrader`` will slowly be including sample (textbook) strategies. Along with
the ``bt-run.py`` script a standard *Simple Moving Average CrossOver* strategy
is included. The name:

  - ``SMA_CrossOver``

  - Parameters

    - fast (default 10) period of the fast moving average
    - slow (default 30) period of the slow moving average

The strategy buys if the fast moving average crosses up the fast and sells (only
if it has bought before) upon the fast moving average crossing down the slow
moving average.

The code

.. literalinclude:: ./sma_crossover.py
   :language: python
   :lines: 21-

Standard execution::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2006-day-001.txt \
	      --plot \
              --strategy :SMA_CrossOver

Notice the ':'. The standard notation (see below) to load a strategy is:

  - module:stragegy:kwargs

With the following rules:

  - If module is there and strategy is specified, then that strategy will be
    used

  - If module is there but no strategy is specified, the 1st strategy found in
    the module will be returned

  - If no module is specified, "strategy" is assumed to refer to a strategy in
    the ``backtrader`` package

  - If module and/or strategy are there, if kwargs are present they will be
    passed to the corresponding strategy

.. note::

   The same notation and rules apply to ``--observer``, ``--analyzer`` and
   ``--indicator`` options

   Obvioously for the corresponding objects type

The output.

.. thumbnail:: ./bt-run-sma-crossover.png

One last example adding commission schemes, cash and changing the parameters::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2006-day-001.txt \
	      --plot \
              --cash 20000 \
              --commission 2.0 \
              --mult 10 \
              --margin 2000 \
              --strategy :SMA_CrossOver:fast=5,slow=20

The output.

.. thumbnail:: ./bt-run-sma-crossover-params-commission.png

We have backtested the strategy:

  - Changing the moving average periods
  - Setting a new starting cash
  - Putting a commission scheme in place for a futures-like instrument

    See the continuous variations in cash with each bar, as cash is adjusted for
    the futures-like instrument daily changes

Using no Strategy
=================

This is a an over-statement. A strategy will be applied, but you can ommit any
kind of strategy and a default backtrader.Strategy will be added.

Analyzers, Observers and Indicators will be automatically injected in the strategy.

An example::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2006-day-001.txt \
              --cash 20000 \
              --commission 2.0 \
              --mult 10 \
              --margin 2000 \
	      --nostdstats \
	      --observer :Broker

This will do not much but serves the purpose:

  - A default backtrader.Strategy is added in the background
  - Cerebro will not instantiate the regular ``stdstats`` observers (Broker,
    BuySell, Trades)
  - A ``Broker`` observer is added manually

Adding Analyzers
================

``bt-run.py`` also supports adding ``Analyzers`` with the same syntax used for
the strategies to choose between internal/external analyzers.

Example with a ``SharpeRatio`` analysis for the years 2005-2006::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2005-2006-day-001.txt \
              --strategy :SMA_CrossOver \
	      --analyzer :SharpeRatio

The console output is **nothing**.

If a printout of the ``Analyzer`` results is wished, it must be specified with:

  - ``--pranalyze`` which defaults to calling the next one (unless the Analyzer
    has overriden the proper method)
  - ``-ppranalyzer`` which uses the ``pprint`` module to print the results

Extending the example from above::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2005-2006-day-001.txt \
              --strategy :SMA_CrossOver \
	      --analyzer :SharpeRatio \
	      --plot \
	      --pranalyzer

  ====================
  == Analyzers
  ====================
  ##########
  sharperatio
  ##########
  {'sharperatio': 11.647332609673256}

Good strategy!!! (Pure luck for the example actually which also bears no
commissions)

The chart (which simply shows the Analyzer is not in the plot, because Analyzers
cannot be plotted, they aren't lines objects)

.. thumbnail:: bt-run-sma-crossover-sharpe.png

Adding Indicators and Observers
===============================

As with ``Strategies`` and ``Analyzers`` bt-run can also add:

  - ``Indicators``

and

  - ``Observers``


The syntax is exactly the same as seen above when adding a ``Broker`` observer.

Let's repeat the example but adding a ``Stochastic``, the ``Broker`` and having
a look at the plot (we'll change some parameters)::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2006-day-001.txt \
	      --nostdstats \
	      --observer :Broker \
	      --indicator :Stochastic:period_dslow=5 \
	      --plot

The chart::

.. thumbnail:: ./bt-run-observer-indicator.png

Plotting Control
================

Most of the above examples have used the following option:

  - ``--plot`` which has activated creating a default plot

More control can be achieved by adding ``kwargs`` to the ``--plot``
option

  - ``--plot style="candle"`` for example to plot with candlesticks instead of
    plotting with a ``LineOnClose`` style (which is the plotting default)

The invocation::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/datas/sample/2006-day-001.txt \
	      --nostdstats \
	      --observer :Broker \
	      --indicator :Stochastic:period_dslow=5 \
	      --plot style=\"candle\"

.. note::

   The quotes around ``candle`` are quoted because the example is being run in a
   bash shell which removes that before passing the arguments to the script.

   Backslash quoting is needed in this case to ensure "bar" makes it to the
   script and can be evaluated as a string

The chart::

.. thumbnail:: ./bt-run-plot-candle.png

Usage of the script
===================

Directly from the script::

  $ ../../backtrader/tools/bt-run.py --help
  usage: bt-run.py [-h] --data DATA
                   [--csvformat {yahoocsv_unreversed,vchart,sierracsv,yahoocsv,vchartcsv,btcsv}]
                   [--fromdate FROMDATE] [--todate TODATE]
                   [--strategy STRATEGIES] [--nostdstats] [--observer OBSERVERS]
                   [--analyzer ANALYZERS] [--pranalyzer | --ppranalyzer]
                   [--indicator module:name:kwargs] [--cash CASH]
                   [--commission COMMISSION] [--margin MARGIN] [--mult MULT]
                   [--plot [kwargs]]

  Backtrader Run Script

  optional arguments:
    -h, --help            show this help message and exit
    --pranalyzer, -pralyzer
                          Automatically print analyzers
    --ppranalyzer, -ppralyzer
                          Automatically PRETTY print analyzers
    --plot [kwargs], -p [kwargs]
                          Plot the read data applying any kwargs passed

                          For example:

                            --plot style="candle" (to plot candlesticks)

  Data options:
    --data DATA, -d DATA  Data files to be added to the system
    --csvformat {yahoocsv_unreversed,vchart,sierracsv,yahoocsv,vchartcsv,btcsv}, -c {yahoocsv_unreversed,vchart,sierracsv,yahoocsv,vchartcsv,btcsv}
                          CSV Format
    --fromdate FROMDATE, -f FROMDATE
                          Starting date in YYYY-MM-DD[THH:MM:SS] format
    --todate TODATE, -t TODATE
                          Ending date in YYYY-MM-DD[THH:MM:SS] format

  Strategy options:
    --strategy STRATEGIES, -st STRATEGIES
                          This option can be specified multiple times.

                          The argument can be specified with the following form:

                            - module:classname:kwargs

                              Example: mymod:myclass:a=1,b=2

                          kwargs is optional

                          If module is omitted then class name will be sought in
                          the built-in strategies module. Such as in:

                            - :name:kwargs or :name

                          If name is omitted, then the 1st strategy found in the
                          will be used. Such as in:

                            - module or module::kwargs

  Observers and statistics:
    --nostdstats          Disable the standard statistics observers
    --observer OBSERVERS, -ob OBSERVERS
                          This option can be specified multiple times.

                          The argument can be specified with the following form:

                            - module:classname:kwargs

                              Example: mymod:myclass:a=1,b=2

                          kwargs is optional

                          If module is omitted then class name will be sought in
                          the built-in observers module. Such as in:

                            - :name:kwargs or :name

                          If name is omitted, then the 1st observer found in the
                          will be used. Such as in:

                            - module or module::kwargs

  Analyzers:
    --analyzer ANALYZERS, -an ANALYZERS
                          This option can be specified multiple times.

                          The argument can be specified with the following form:

                            - module:classname:kwargs

                              Example: mymod:myclass:a=1,b=2

                          kwargs is optional

                          If module is omitted then class name will be sought in
                          the built-in analyzers module. Such as in:

                            - :name:kwargs or :name

                          If name is omitted, then the 1st analyzer found in the
                          will be used. Such as in:

                            - module or module::kwargs

  Indicators:
    --indicator module:name:kwargs, -ind module:name:kwargs
                          This option can be specified multiple times.

                          The argument can be specified with the following form:

                            - module:classname:kwargs

                              Example: mymod:myclass:a=1,b=2

                          kwargs is optional

                          If module is omitted then class name will be sought in
                          the built-in analyzers module. Such as in:

                            - :name:kwargs or :name

                          If name is omitted, then the 1st analyzer found in the
                          will be used. Such as in:

                            - module or module::kwargs

  Cash and Commission Scheme Args:
    --cash CASH, -cash CASH
                          Cash to set to the broker
    --commission COMMISSION, -comm COMMISSION
                          Commission value to set
    --margin MARGIN, -marg MARGIN
                          Margin type to set
    --mult MULT, -mul MULT
                          Multiplier to use

And the code:

.. literalinclude:: ../tools/bt-run.py
   :language: python
   :lines: 21-

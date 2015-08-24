
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
              --data ../samples/data/sample/2006-day-001.txt \
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
              --data ../samples/data/sample/2006-day-001.txt \
              --strategy ./mymod.py \
              period 50

The chart output.

.. thumbnail:: ./bt-run-mymod-period-50.png

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
              --data ../samples/data/sample/2006-day-001.txt \
              --strategy :SMA_CrossOver

Notice the ':'. The standard notation (see below) to load a strategy is:

  - module:stragegy

With the following rules:

  - If module is there and strategy is specified, then that strategy will be
    used

  - If module is there but no strategy is specified, the 1st strategy found in
    the module will be returned

  - If no module is specified, "strategy" is assumed to refer to a strategy in
    the ``backtrader`` package

The latter being our case.

The output.

.. thumbnail:: ./bt-run-sma-crossover.png

One last example adding commission schemes, cash and changing the parameters::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/data/sample/2006-day-001.txt \
              --cash 20000 \
              --commission 2.0 \
              --mult 10 \
              --margin 2000 \
              --strategy :SMA_CrossOver \
              fast 5 slow 20

The output.

.. thumbnail:: ./bt-run-sma-crossover-params-commission.png

We have backtested the strategy:

  - Changing the moving average periods
  - Setting a new starting cash
  - Putting a commission scheme in place for a futures-like instrument

    See the continuous variations in cash with each bar, as cash is adjusted for
    the futures-like instrument daily changes

Adding Analyzers
================

``bt-run.py`` also supports adding ``Analyzers`` with the same syntax used for
the strategies to choose between internal/external analyzers.

Example with a ``SharpeRatio`` analysis for the years 2005-2006::

  ./bt-run.py --csvformat btcsv \
              --data ../samples/data/sample/2005-2006-day-001.txt \
              --strategy :SMA_CrossOver \
	      --analyzer :SharpeRatio

The output::

  ====================
  == Analyzers
  ====================
  ##  sharperatio
  --  sharperatio : 11.6473326097

Good strategy!!! (Pure luck for the example actually which also bears no
commissions)

The chart (which simply shows the Analyzer is not in the plot, because Analyzers
cannot be plotted, they aren't lines objects)

.. thumbnail:: bt-run-sma-crossover-sharpe.png

Usage of the script
===================

Directly from the script::

  $ ./bt-run.py --help
  usage: bt-run.py [-h] --data DATA
                   [--csvformat {yahoocsv_unreversed,vchart,sierracsv,yahoocsv,vchartcsv,btcsv}]
                   [--fromdate FROMDATE] [--todate TODATE] --strategy STRATEGY
                   [--nostdstats] [--observer OBSERVERS] [--analyzer ANALYZERS]
                   [--cash CASH] [--commission COMMISSION] [--margin MARGIN]
                   [--mult MULT] [--noplot] [--plotstyle {bar,line,candle}]
                   [--plotfigs PLOTFIGS]
                   ...

  Backtrader Run Script

  positional arguments:
    args                  args to pass to the loaded strategy

  optional arguments:
    -h, --help            show this help message and exit

  Data options:
    --data DATA, -d DATA  Data files to be added to the system
    --csvformat {yahoocsv_unreversed,vchart,sierracsv,yahoocsv,vchartcsv,btcsv}, -c {yahoocsv_unreversed,vchart,sierracsv,yahoocsv,vchartcsv,btcsv}
                          CSV Format
    --fromdate FROMDATE, -f FROMDATE
                          Starting date in YYYY-MM-DD[THH:MM:SS] format
    --todate TODATE, -t TODATE
                          Ending date in YYYY-MM-DD[THH:MM:SS] format

  Strategy options:
    --strategy STRATEGY, -st STRATEGY
                          Module and strategy to load with format
                          module_path:strategy_name. module_path:strategy_name
                          will load strategy_name from the given module_path
                          module_path will load the module and return the first
                          available strategy in the module :strategy_name will
                          load the given strategy from the set of built-in
                          strategies

  Observers and statistics:
    --nostdstats          Disable the standard statistics observers
    --observer OBSERVERS, -ob OBSERVERS
                          This option can be specified multiple times Module and
                          observer to load with format
                          module_path:observer_name. module_path:observer_name
                          will load observer_name from the given module_path
                          module_path will load the module and return all
                          available observers in the module :observer_name will
                          load the given strategy from the set of built-in
                          strategies

  Analyzers:
    --analyzer ANALYZERS, -an ANALYZERS
                          This option can be specified multiple times Module and
                          analyzer to load with format
                          module_path:analzyer_name. module_path:analyzer_name
                          will load observer_name from the given module_path
                          module_path will load the module and return all
                          available analyzers in the module :anaylzer_name will
                          load the given strategy from the set of built-in
                          strategies

  Cash and Commission Scheme Args:
    --cash CASH, -cash CASH
                          Cash to set to the broker
    --commission COMMISSION, -comm COMMISSION
                          Commission value to set
    --margin MARGIN, -marg MARGIN
                          Margin type to set
    --mult MULT, -mul MULT
                          Multiplier to use

  Plotting options:
    --noplot, -np         Do not plot the read data
    --plotstyle {bar,line,candle}, -ps {bar,line,candle}
                          Plot style for the input data
    --plotfigs PLOTFIGS, -pn PLOTFIGS
                          Plot using n figures

And the code:

.. literalinclude:: ./bt-run.py
   :language: python
   :lines: 21-

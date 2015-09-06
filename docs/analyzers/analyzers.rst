
Analyzers
#########

Observers already cover the generation of visual feedback and can also calculate
statistics (like the ``DrawDown`` observer)

The are ``Lines`` objects so they have, obviously, ``lines`` which consume
memory and procesing time and somtimes are not needed.

Sometimes too, statistics cannot be generated until processing has come to an
end and therefore ``Observers`` are not fit for the purpose.

It is when ``Analyzers`` come into play. Classic example:

  - `SharpeRatio <https://en.wikipedia.org/wiki/Sharpe_ratio>`_

    Although Wikipedia talks about the Ex-Ante, the real world cares about the
    Ex-Post (the real ratio after the strategy has been executed)

The SharpeRatio needs 2 or more "AnnualReturns" to calculate something, i.e.:

  - It has to wait until the Strategy execution has come to an end

Using Analyzers
===============

It follows the same model as ``datas``, ``strategies`` and ``observers``

  - Add them via the ``cerebro`` instance, with some arguments if wished and it
    will be silently added to the strategy and to the calculation queues.

Example::

  from __future__ import (absolute_import, division, print_function,
                          unicode_literals)

  import datetime

  import backtrader as bt
  import backtrader.analyzers as btanalyzers
  import backtrader.feeds as btfeeds
  import backtrader.strategies as btstrats

  cerebro = bt.Cerebro()

  # data
  dataname = '../datas/sample/2005-2006-day-001.txt'
  data = btfeeds.BacktraderCSVData(dataname=dataname)

  cerebro.adddata(data)

  # strategy
  cerebro.addstrategy(btstrats.SMA_CrossOver)

  # Analyzer
  cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe')

  thestrats = cerebro.run()
  thestrat = thestrats[0]

  print('Sharpe Ratio:', thestrat.analyzers.mysharpe.get_analysis())

Executing it::

  $ ./analyzer-test.py
  Sharpe Ratio: {'sharperatio': 11.647332609673256}

There is no plotting, because the ``SharpeRatio`` is a single value at the end
of the calculation.


Forensic Analysis of an Analyzer
================================

Let's repeat that ``Analyzers`` are not Lines objects, but to seamlessly
integrate them into the ``backtrader`` ecosystem, it follows the internal API
conventions of several Lines object, actually a **mixture** of them.

Code for ``SharpeRatio`` to serve as a basis.

.. literalinclude:: ./sharpe-forensic.py
   :language: python
   :lines: 21-

The code is broken down into:

  - Member Attributes:

    ``strategy``

    Analyzers have automatically this member attribute which gives the analyzer
    direct access to the parent strategy.

  - ``params`` declaration

    Although the declared ones are not used (future-proof), Analyzers like most
    other objects in ``backtrader`` support parameters

  - ``__init__`` method

    Just like ``Strategies`` declare ``Indicators`` in ``__init__``, the same do
    analyzers with support objects.

    In this case: the SharpeRatio is calculated using ``Annual Returns``. The
    calculation will be automatic and will be available to ``SharpeRatio`` for
    its own calculations.

  - ``next`` method

    ``SharpeRatio`` doesn't need it, but this method will be called afte each
    invocation of the parent strategy ``next``

  - ``start`` method

    Called right before the backtesting starts. Can be used for extra
    initialization tasks. Sharperatio doesn't need it

  - ``stop`` method

    Called right after the backtesting ends. Like ``SharpeRatio`` does, it can
    be used to finish/make the calculation

  - ``get_analysis`` method (returns a dictionary)

    Access for external callers to the produced analysis

    Returns: a dictionary with the analysis.

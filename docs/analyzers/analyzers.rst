Analyzers
#########

Be it backtesting or trading, being able to analyze the performance of the
trading system is key to understanding if not only profit has been attained,
but also if it has been achieved with too much risk or if it was really worth
the effort when compared with a reference asset (or a risk-free asset)

That's where the family of ``Analyzer`` objects comes in: provide an analysis
of what's happened or even of what's actually happening.

Nature of analyzers
===================

The interface is modeled after that of *Lines* objects, feature for example a
``next`` method but there is a major difference:

  - ``Analyzers`` do not hold lines.

    That means they are not expensive in terms of memory because even after
    having analyzed thousands of price bars they may still simply hold a single
    result in memory.

Location in the ecosystem
=========================

``Analyzer`` objects are (like *strategies*, *observers* and *datas*) added to
the system through a ``cerebro`` instance:

  - ``addanalyzer(ancls, *args, **kwargs)``

But when it comes to operation during ``cerebro.run`` the following will happen
for each *strategy* present in the system

  - ``ancls`` will be instantiated with ``*args`` and ``**kwargs`` during a ``cerebro.run``

  - The ``ancls`` instance will be attached to the strategy

That means:

  - If the backtesting run contains for example *3 strategies* then *3
    instances* of ``ancls`` will be created and each of them will be attached
    to a different strategy.

Bottomline: *an analyzer analyzes the performance of a single strategy* and
*not the performance of an entires system*

Additional Location
-------------------

Some ``Analyzer`` objects may actually use other analyzers to complete its
work. For example: ``SharpeRatio`` uses the output of ``TimeReturn`` for the
calculations.

These *sub-analyzers* or *slave-analyzers* will also be inserted into the same
strategy as the one creating them. But they are completely invisible to the user.


Attributes
==========

To carry out the intended work, ``Analyzer`` objects are provided with some
default attributes which are automagically passed and set in the instance for
ease of use:

  - ``self.strategy``: reference to the strategy subclass in which the
    analyzer object is operating.  Anything accessible by the *strategy* can
    also be accessd by the *analyzer*

  - ``self.datas[x]``: the array of data feeds present in the
    strategy. Although this could be accesed over the *strategy* reference, the
    shortcut makes work more comfortable.

  - ``self.data``: shortcut to ``self.datas[0]`` for extra comfort.

  - ``self.dataX``: shortcuts to the different ``self.datas[x]``

  Some other aliases are available although they are probably an overkill:

    - ``self.dataX_Y`` where X is a reference to ``self.datas[X]`` and ``Y``
      refers to the line, finally pointing to: ``self.datas[X].lines[Y]``

  If the line has a name, the following is also available:

    - ``self.dataX_Name`` which resolves to ``self.datas[X].Name`` returning
      the line by name rather than by index

  For the first data, the last two shortcuts are available without the initial
  ``X`` numeric reference. For example:

    - ``self.data_2`` refers to ``self.datas[0].lines[2]``

  And

    - ``self.data_close`` refers to ``self.datas[0].close``

Returning the analysis
----------------------

The *Analyzer* base class creates a ``self.rets`` (of type
``collections.OrderedDict``) member attribute to return the analysis. This is
done in the method ``create_analysis`` which can be overriden by subclasses if
creating custom analyzers.


Modus operandi
==============

Although ``Analyzer`` objects are not *Lines* objects and therefore do not
iterate over lines, they have been designed to follow the same operation
pattern.

  #.  Instantiated before the system is put into motion (therefore calling
      ``__init__``)

  #. Signaled the begin of operations with ``start``

  #. ``prenext`` / ``nextstart`` / ``next`` will be invoked following the
     calculated minimum period of the *strategy* the indicator is working in.

     The default behaviour of ``prenext`` and ``nextstart`` is to invoke next,
     because an analyzer may be analyzing from the very first moment the system
     is alive.

     It may be customary to call ``len(self)`` in *Lines* objects to check the
     actual amount of bars. This also works in ``Analyzers`` by returning the
     value for ``self.strategy``

  #. Orders and trades will be notified just like they are to the strategy via
     ``notify_order`` and ``notify_trade``

  #. Cash and value will also be notified like it is done with the strategy
     over the ``notify_cashvalue`` method

  #. ``stop`` will be invoked to signal the end of operations

Once the regular operations cycle has been completed, the *analyzers* featuring
additional methods for extracting/outputting information

  - ``get_analysis``: which ideally (not enforced) returnes a ``dict`` -like
    object containing the analysis results.

  - ``print`` uses a standard ``backtrader.WriterFile`` (unless overriden) to
    write the analysis result from ``get_analysis``.

  - ``pprint`` (*pretty print*) uses the Python ``pprint`` module to print the
    ``get_analysis`` resutls.

And finally:

  - ``get_analysis`` creates a member attribute ``self.ret`` (of type
    ``collections.OrderedDict``) to which analyzers write the analysis results.

    Subclasses of *Analyzer* can override this method to change this behavior

Analyzer Patterns
=================

Development of *Analyzer* objects in the ``backtrader`` platform have revealed
2 different usage patterns for the generation of the analysis:

  #. During execution by gathering information in the ``notify_xxx`` and
     ``next`` methods, and generating the current information of the analysis
     in ``next``

     The ``TradeAnalyzer``, for example, uses just the ``notify_trade`` method
     to generate the statistics.

  #. Gather (or not) the information as above, but generate the analysis in a
     single pass during the ``stop`` method

     The ``SQN`` (*System Quality Number*) gathers trade information during
     ``notify_trade`` but generates the statistic during the ``stop`` method


A quick example
===============

As easy as it can be::

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

Executing it (having stored it in ``analyzer-test.py``::

  $ ./analyzer-test.py
  Sharpe Ratio: {'sharperatio': 11.647332609673256}

There is no plotting, because the ``SharpeRatio`` is a single value at the end
of the calculation.


Forensic Analysis of an Analyzer
================================

Let's repeat that ``Analyzers`` are not Lines objects, but to seamlessly
integrate them into the ``backtrader`` ecosystem, the internal API conventions
of several Lines object are followed (actually a **mixture** of them)

.. note:: The code for the ``SharpeRatio`` has evolved to take for example into
	  account annualization and the version here should only be a
	  reference.

	  Please check the :doc:`../analyzers-reference`

	  There is additionally a ``SharpeRatio_A`` which provides the value
	  directly in annualized form regardless of the sought timeframe

Code for ``SharpeRatio`` to serve as a basis (a simplified version)

.. literalinclude:: ./sharpe-forensic.py
   :language: python
   :lines: 21-

The code can be broken down into:

  - ``params`` declaration

    Although the declared ones are not used (meant as an example), *Analyzers*
    like most other objects in ``backtrader`` support parameters

  - ``__init__`` method

    Just like *Strategies* declare *Indicators* in ``__init__``, the same do
    analyzers with support objects.

    In this case: the ``SharpeRatio`` is calculated using **Annual Returns**. The
    calculation will be automatic and will be available to ``SharpeRatio`` for
    its own calculations.

    .. note:: The actual implementation of ``SharpeRatio`` uses the more
	      generic and later developed ``TimeReturn`` analyzer

  - ``next`` method

    ``SharpeRatio`` doesn't need it, but this method will be called after each
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


Reference
=========

.. currentmodule:: backtrader

.. autoclass:: Analyzer

   .. automethod:: start

   .. automethod:: stop

   .. automethod:: prenext

   .. automethod:: nextstart

   .. automethod:: next

   .. automethod:: notify_cashvalue

   .. automethod:: notify_order

   .. automethod:: notify_trade

   .. automethod:: get_analysis

   .. automethod:: create_analysis

   .. automethod:: print

   .. automethod:: pprint

   .. automethod:: __len__

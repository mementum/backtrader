
Strategy with Signals
#####################

Operating *backtrader* is also possible without having to write a
*Strategy*. Although this is the preferred way, due to the object hierarchy
which makes up the machinery, using *Signals* is also possible.

Quick summary:

  - Instead of writing a *Strategy* class, instantiating *Indicators*, writing
    the *buy/sell* logic ...

  - The end user add *Signals* (indicators anyhow) and the rest is done in the
    background

Quick example::

  import backtrader as bt

  data = bt.feeds.OneOfTheFeeds(dataname='mydataname')
  cerebro.adddata(data)

  cerebro.add_signal(bt.SIGNAL_LONGSHORT, MySignal)
  cerebro.run()

Et voilá!.

Of course the *Signal* itself is missing. Let's define a very dumb *Signal*
which yields:

  - ``Long`` indication if the ``close`` price is above a *Simple Moving
    Average*

  - ``Short`` indication if the ``close`` price is below a *Simple Moving
    Average*

The definition::

  class MySignal(bt.Indicator):
      lines = ('signal',)
      params = (('period', 30),)

      def __init__(self):
          self.lines.signal = self.data - bt.indicators.SMA(period=self.p.period)

And now it is really done. When ``run`` is executed *Cerebro* will take care of
instantiating a special *Strategy* instance which knows what to do with the
*Signals*.

Initial *FAQ*
=============

  - How is the volume of *buy*/*sell* operations determined?

    A *cerebro* instance adds automatically a ``FixedSize`` sizer to
    strategies. The end user can change the sizer to alter the policy with
    ``cerebro.addsizer``

  - How are orders executed?

    The execution type is ``Market`` and the validity is *Good Until Canceled*


*Signals* technicalities
========================

From a technical and theoretical point of view can be as described:

  - A callable that returns another *object* when called (only once)

    This is in most cases the instantiation of a class, but must not be

  - Supports the ``__getitem__`` interface. The only requested *key*/*index*
    will be ``0``

From a practical point of view and looking at the example above a *Signal* is:

  - A *lines* object from the *backtrader* ecosystem, mostly an *Indicator*

    This helps when using other *Indicators* like when in the example the *Simple
    Moving Average* is used.


*Signals* indications
=====================

The *signals* delivers indications when queried with ``signal[0]`` and the
meaning is:

  - ``> 0`` -> ``long indication``

  - ``< 0`` -> ``short indication``

  - ``== 0`` -> *No indication*

The example does simple arithmetic with ``self.data - SMA`` and:

  - Issues a ``long indication`` when the ``data`` is above the ``SMA``

  - Issues a ``short indication`` when the ``data`` is below the ``SMA``

.. note:: When no specific price field is indicated for the ``data``, the
	  ``close`` price is the reference price is.

*Signals* Types
===============

The *constants* indicated below as seen in the example above, are directly
available from the main *backtrader* module as in::

  import backtrader as bt

  bt.SIGNAL_LONG

There are 5 types of *Signals*, broken in 2 groups.

**Main Group**:

  - ``LONGSHORT``: both ``long`` and ``short`` indications from this signal
    are taken

  - ``LONG``:

    - ``long`` indications are taken to go long
    - ``short`` indications are taken to *close* the long position. But:

      - If a ``LONGEXIT`` (see below) signal is in the system it will be
        used to exit the long

      - If a ``SHORT`` signal is available and no ``LONGEXIT`` is available
        , it will be used to close a ``long`` before opening a ``short``

  - ``SHORT``:

    - ``short`` indications are taken to go short
    - ``long`` indications are taken to *close* the short position. But:

      - If a ``SHORTEXIT`` (see below) signal is in the system it will be
        used to exit the short

      - If a ``LONG`` signal is available and no ``SHORTEXIT`` is available
        , it will be used to close a ``short`` before opening a ``long``

**Exit Group**:

  This 2 signals are meant to override others and provide criteria for
  exitins a ``long`` / ``short`` position

  - ``LONGEXIT``: ``short`` indications are taken to exit ``long``
    positions

  - ``SHORTEXIT``: ``long`` indications are taken to exit ``short``
    positions


Accumulation and Order Concurrency
==================================

The sample *Signal* shown above will issue *long* and *short* indications on a
constant basis, because it simply substracts the ``SMA`` value from the
``close`` price and this will always be either ``> 0`` and ``< 0`` ( ``0`` is
mathematically possible, but unlikely to really happen)

This would lead to a continuous generation of *orders* that would produce 2
situations:

  - ``Accumulation``: even if already in the market, the *signals* would
    produce new orders which would increase the possition in the market

  - ``Concurrency``: new orders would be generated without waiting for the
    execution of other orders

To avoid this the default behavior is:

  - *To Not Accumulate*

  - *To Not allow Concurrency*

Should any of these two behaviors be wished, this can be controlled via
``cerebro`` with:

  - ``cerebro.signal_accumulate(True)`` (or ``False`` to re-disable it)

  - ``cerebro.signal_concurrency(True)`` (or ``False`` to re-disable it)


The sample
==========

The *backtrader* sources contain a sample to test the functionality.

Main signal to be used.

.. literalinclude:: ../../samples/signals-strategy/signals-strategy.py
   :language: python
   :lines: 43-49

And the *Exit Signal* in case the option is specified.

.. literalinclude:: ../../samples/signals-strategy/signals-strategy.py
   :language: python
   :lines: 51-59

First run: long and short
-------------------------
::

  $ ./signals-strategy.py --plot --signal longshort

The output

.. thumbnail:: signal-longshort.png

To notice:

  - The *Signal* is plotted. This is normal given it is simply an indicator and
    the plotting rules for it apply

  - The strategy is really ``long`` and ``short``. This can be seen because the
    *cash* level never goes back to be the *value* level

  - Side note: even for a dumb idea ... (and without commission) the strategy
    hasn't lost money ...


Second run: long only
---------------------
::

  $ ./signals-strategy.py --plot --signal longonly

The output

.. thumbnail:: signal-longonly.png

To notice:

  - Here the cash level goes back to be the *value* level after each *sell*,
    which means the strategy is out of the market

  - Side note: Again no money has been lost ...

Third run: short only
---------------------
::

  $ ./signals-strategy.py --plot --signal shortonly

The output

.. thumbnail:: signal-shortonly.png

To notice:

  - The 1st operation is a *sell* as expected and takes place later than the
    1st operation in the 2 examples above. Not until the ``close`` is below
    the ``SMA`` and the simple substraction yields a minus

  - Here the cash level goes back to be the *value* level after each *buy*,
    which means the strategy is out of the market

  - Side note: Finally the system loses money


Fourth run: long + longexit
---------------------------
::

  $ ./signals-strategy.py --plot --signal longonly --exitsignal longexit

The output

.. thumbnail:: signal-long-longexit.png

To notice:

  - Many of the trades are the same, but some are interrupted earlier because
    the fast moving average in the *exit* signal crosses the slow moving average
    to the downside

  - The system shows its *longonly* property with the cash becoming the value
    at the end of each trade

  - Side note: Again money is made ... even with some modified trades

Usage
-----
::

  $ ./signals-strategy.py --help
  usage: signals-strategy.py [-h] [--data DATA] [--fromdate FROMDATE]
                             [--todate TODATE] [--cash CASH]
                             [--smaperiod SMAPERIOD] [--exitperiod EXITPERIOD]
                             [--signal {longshort,longonly,shortonly}]
                             [--exitsignal {longexit,shortexit}]
                             [--plot [kwargs]]

  Sample for Signal concepts

  optional arguments:
    -h, --help            show this help message and exit
    --data DATA           Specific data to be read in (default:
                          ../../datas/2005-2006-day-001.txt)
    --fromdate FROMDATE   Starting date in YYYY-MM-DD format (default: None)
    --todate TODATE       Ending date in YYYY-MM-DD format (default: None)
    --cash CASH           Cash to start with (default: 50000)
    --smaperiod SMAPERIOD
                          Period for the moving average (default: 30)
    --exitperiod EXITPERIOD
                          Period for the exit control SMA (default: 5)
    --signal {longshort,longonly,shortonly}
                          Signal type to use for the main signal (default:
                          longshort)
    --exitsignal {longexit,shortexit}
                          Signal type to use for the exit signal (default: None)
    --plot [kwargs], -p [kwargs]
                          Plot the read data applying any kwargs passed For
                          example: --plot style="candle" (to plot candles)
                          (default: None)


The code
--------

.. literalinclude:: ../../samples/signals-strategy/signals-strategy.py
   :language: python
   :lines: 21-

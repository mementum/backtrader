TA-Lib
######

Even if *backtrader* offers an already high number of built-in indicators and
developing an indicator is mostly a matter of defining the inputs, outputs and
writing the formula in a natural manner, some people want to use *TA-LIB*. Some
of the reasons:

  - Indicator *X* is in the library and not in *backtrader* (the author would
    gladly accept a request)

  - *TA-LIB* behavior is well known and people trust good old things

In order to satisfy each and every taste, *TA-LIB* integration is offered.

Requirements
************

  - `Python wrapper for TA-Lib <https://github.com/mrjbq7/ta-lib>`_

  - Any dependencies needed by it (for example *numpy*)

The installation details are on the *GitHub* repository


Using *ta-lib*
**************

As easy as using any of the indicators already built-in in
*backtrader*. Example of a *Simple Moving Average*. First the *backtrader*
one::

  import backtrader as bt

  class MyStrategy(bt.Strategy):
      params = (('period', 20),)

      def __init__(self):
          self.sma = bt.indicators.SMA(self.data, period=self.p.period)
	  ...

  ...

Now the *ta-lib* example::

  import backtrader as bt

  class MyStrategy(bt.Strategy):
      params = (('period', 20),)

      def __init__(self):
          self.sma = bt.talib.SMA(self.data, timeperiod=self.p.period)
	  ...

  ...

Et voilá! Of course the *params* for the *ta-lib* indicators are defined by the
library itself and not by *backtrader*. In this case the *SMA* in *ta-lib*
takes a parameter named ``timeperiod`` to defined the size of the operating
window.

For indicators that require more than one input, for example the *Stochastic*::

  import backtrader as bt

  class MyStrategy(bt.Strategy):
      params = (('period', 20),)

      def __init__(self):
          self.stoc = bt.talib.STOCH(self.data.high, self.data.low, self.data.close,
                                     fastk_period=14, slowk_period=3, slowd_period=3)

	  ...

  ...

Notice how ``high``, ``low`` and ``close`` have been individually passed. One
could always pass ``open`` instead of ``low`` (or any other data series) and
experiment.

The *ta-lib* indicator documentation is automatically parsed and added to the
*backtrader* docs. You may also check the *ta-lib* source code/docs. Or
adittionally do::

  print(bt.talib.SMA.__doc__)

Which in this case outputs::

  SMA([input_arrays], [timeperiod=30])

  Simple Moving Average (Overlap Studies)

  Inputs:
      price: (any ndarray)
  Parameters:
      timeperiod: 30
  Outputs:
      real

Which offers some information:

  - Which *Input* is to be expected (*DISREGARD the ``ndarray`` comment* because
    backtrader manages the conversions in the background)

  - Which *parameters* and which default values

  - Which output *lines* the indicator actually offers

Moving Averages and MA_Type
===========================

To select a specific *moving average* for indicators like ``bt.talib.STOCH``,
the standard *ta-lib* ``MA_Type`` is accesible with
``backtrader.talib.MA_Type``. For example::

  import backtrader as bt
  print('SMA:', bt.talib.MA_Type.SMA)
  print('T3:', bt.talib.MA_Type.T3)


Plotting ta-lib indicators
**************************

Just as with regular usage, there is nothing special to do to plot the *ta-lib*
indicators.

.. note:: Indicators which output a *CANDLE* (all those looking for a
	  candlestick pattern) deliver a binary output: either 0 or 100. In
	  order to avoid adding a ``subplot`` to the chart, there is an
	  automated plotting translation to plot them over the *data* at the
	  point in time in which the pattern was recognized.

Examples and comparisons
************************

The following are plots comparing the outputs of some *ta-lib* indicators
against the equivalent built-in indicators in *backtrader*. To consider:

  - The *ta-lib* indicators get a ``TA_`` prefix on the plot. This is
    specifically done by the sample to help the user spot which is which

  - *Moving Averages* (if both deliver the same result) will be plotted *ON*
    top of the other existing *Moving Average*. The two indicators cannot be
    seen separately and the test is a pass if that's the case.

  - All samples include a ``CDLDOJI`` indicator as a reference

KAMA (Kaufman Moving Average)
=============================

This is the 1st example because it is the only (from all indicators which the
sample directly compare) that has a difference:

  - The initial values of the the samples are not the same

  - At some point in time, the values converge and both *KAMA* implementations
    have the same behavior.

After having analyzed the *ta-lib* source code:

  - The implementation in *ta-lib* makes a non-industry standard choice for the
    1st values of the *KAMA*.

    The choice can be seen in the source code quoting from the source code):
    *The yesterday price is used here as the previous KAMA.*

*backtrader* does the usual choice which is the same as for example the one
from *Stockcharts*:

  - `KAMA at StockCharts
    <http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:kaufman_s_adaptive_moving_average>`_

    *Since we need an initial value to start the calculation, the first KAMA is
    just a simple moving average*

Hence the difference. Furthermore:

  - The *ta-lib* ``KAMA`` implementation doesn't allow specifying the ``fast``
    and ``slow`` periods for the adjustment of the *scalable constant* defined
    by *Kaufman*.

Sample execution::

  $ ./talibtest.py --plot --ind kama

Output

.. thumbnail:: ta-lib-kama.png

SMA
===
::

  $ ./talibtest.py --plot --ind sma

Output

.. thumbnail:: ta-lib-sma.png

EMA
===
::

  $ ./talibtest.py --plot --ind ema

Output

.. thumbnail:: ta-lib-ema.png

Stochastic
==========
::

  $ ./talibtest.py --plot --ind stoc

Output

.. thumbnail:: ta-lib-stoc.png

RSI
===
::

  $ ./talibtest.py --plot --ind rsi

Output

.. thumbnail:: ta-lib-rsi.png

MACD
====
::

  $ ./talibtest.py --plot --ind macd

Output

.. thumbnail:: ta-lib-macd.png

Bollinger Bands
===============
::

  $ ./talibtest.py --plot --ind bollinger

Output

.. thumbnail:: ta-lib-bollinger.png

AROON
=====

Note that *ta-lib* chooses to put the *down* line first and the colours are
inverted when compared with the *backtrader* built-in indicator.
::

  $ ./talibtest.py --plot --ind aroon

Output

.. thumbnail:: ta-lib-aroon.png

Ultimate Oscillator
===================
::

  $ ./talibtest.py --plot --ind ultimate

Output

.. thumbnail:: ta-lib-ultimate.png

Trix
====
::

  $ ./talibtest.py --plot --ind trix

Output

.. thumbnail:: ta-lib-trix.png

ADXR
====
Here *backtrader* offers both the ``ADX`` and ``ADXR`` lines.

::

  $ ./talibtest.py --plot --ind adxr

Output

.. thumbnail:: ta-lib-adxr.png

DEMA
====
::

  $ ./talibtest.py --plot --ind dema

Output

.. thumbnail:: ta-lib-dema.png

TEMA
====
::

  $ ./talibtest.py --plot --ind tema

Output

.. thumbnail:: ta-lib-tema.png

PPO
===

Here *backtrader* offers not only the ``ppo`` line, but a more traditional
``macd`` approach.
::

  $ ./talibtest.py --plot --ind ppo

Output

.. thumbnail:: ta-lib-ppo.png

WilliamsR
=========
::

  $ ./talibtest.py --plot --ind williamsr

Output

.. thumbnail:: ta-lib-williamsr.png

ROC
===
All indicators show have exactly the same shape, but how to track *momentum* or
*rate of change* has several definitions
::

  $ ./talibtest.py --plot --ind roc

Output

.. thumbnail:: ta-lib-roc.png

Sample Usage
************
::

  $ ./talibtest.py --help
  usage: talibtest.py [-h] [--data0 DATA0] [--fromdate FROMDATE]
                      [--todate TODATE]
                      [--ind {sma,ema,stoc,rsi,macd,bollinger,aroon,ultimate,trix,kama,adxr,dema,tema,ppo,williamsr,roc}]
                      [--no-doji] [--use-next] [--plot [kwargs]]

  Sample for ta-lib

  optional arguments:
    -h, --help            show this help message and exit
    --data0 DATA0         Data to be read in (default:
                          ../../datas/yhoo-1996-2015.txt)
    --fromdate FROMDATE   Starting date in YYYY-MM-DD format (default:
                          2005-01-01)
    --todate TODATE       Ending date in YYYY-MM-DD format (default: 2006-12-31)
    --ind {sma,ema,stoc,rsi,macd,bollinger,aroon,ultimate,trix,kama,adxr,dema,tema,ppo,williamsr,roc}
                          Which indicator pair to show together (default: sma)
    --no-doji             Remove Doji CandleStick pattern checker (default:
                          False)
    --use-next            Use next (step by step) instead of once (batch)
                          (default: False)
    --plot [kwargs], -p [kwargs]
                          Plot the read data applying any kwargs passed For
                          example (escape the quotes if needed): --plot
                          style="candle" (to plot candles) (default: None)

Sample Code
***********

.. literalinclude:: ../../samples/talib/talibtest.py
   :language: python
   :lines: 21-

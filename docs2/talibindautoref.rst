
TA-Lib Indicator Reference
==========================

.. .. talibindref::


TA-Lib Indicator Reference
**************************

ACOS

ACOS([input_arrays])

Vector Trigonometric ACos (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

AD

AD([input_arrays])

Chaikin A/D Line (Volume Indicators)

Inputs:
   prices: ['high', 'low', 'close', 'volume']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ADD

ADD([input_arrays])

Vector Arithmetic Add (Math Operators)

Inputs:
   price0: (any ndarray) price1: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ADOSC

ADOSC([input_arrays], [fastperiod=3], [slowperiod=10])

Chaikin A/D Oscillator (Volume Indicators)

Inputs:
   prices: ['high', 'low', 'close', 'volume']

Parameters:
   fastperiod: 3 slowperiod: 10

Outputs:
   real

Lines:
   * real

Params:
   * fastperiod (3)

   * slowperiod (10)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ADX

ADX([input_arrays], [timeperiod=14])

Average Directional Movement Index (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ADXR

ADXR([input_arrays], [timeperiod=14])

Average Directional Movement Index Rating (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

APO

APO([input_arrays], [fastperiod=12], [slowperiod=26], [matype=0])

Absolute Price Oscillator (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   fastperiod: 12 slowperiod: 26 matype: 0 (Simple Moving Average)

Outputs:
   real

Lines:
   * real

Params:
   * fastperiod (12)

   * slowperiod (26)

   * matype (0)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

AROON

AROON([input_arrays], [timeperiod=14])

Aroon (Momentum Indicators)

Inputs:
   prices: ['high', 'low']

Parameters:
   timeperiod: 14

Outputs:
   aroondown aroonup

Lines:
   * aroondown

   * aroonup

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * aroondown: - ls (--)

   * aroonup: - ls (-)

AROONOSC

AROONOSC([input_arrays], [timeperiod=14])

Aroon Oscillator (Momentum Indicators)

Inputs:
   prices: ['high', 'low']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ASIN

ASIN([input_arrays])

Vector Trigonometric ASin (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ATAN

ATAN([input_arrays])

Vector Trigonometric ATan (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ATR

ATR([input_arrays], [timeperiod=14])

Average True Range (Volatility Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

AVGPRICE

AVGPRICE([input_arrays])

Average Price (Price Transform)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

BBANDS

BBANDS([input_arrays], [timeperiod=5], [nbdevup=2], [nbdevdn=2],
[matype=0])

Bollinger Bands (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 5 nbdevup: 2 nbdevdn: 2 matype: 0 (Simple Moving
   Average)

Outputs:
   upperband middleband lowerband

Lines:
   * upperband

   * middleband

   * lowerband

Params:
   * timeperiod (5)

   * nbdevup (2)

   * nbdevdn (2)

   * matype (0)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * middleband: - _samecolor (True) - ls (-)

   * upperband:

   * lowerband: - _samecolor (True)

BETA

BETA([input_arrays], [timeperiod=5])

Beta (Statistic Functions)

Inputs:
   price0: (any ndarray) price1: (any ndarray)

Parameters:
   timeperiod: 5

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (5)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

BOP

BOP([input_arrays])

Balance Of Power (Momentum Indicators)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

CCI

CCI([input_arrays], [timeperiod=14])

Commodity Channel Index (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

CDL2CROWS

CDL2CROWS([input_arrays])

Two Crows (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDL2CROWS)

CDL3BLACKCROWS

CDL3BLACKCROWS([input_arrays])

Three Black Crows (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDL3BLACKCROWS)

CDL3INSIDE

CDL3INSIDE([input_arrays])

Three Inside Up/Down (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDL3INSIDE)

CDL3LINESTRIKE

CDL3LINESTRIKE([input_arrays])

Three-Line Strike  (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDL3LINESTRIKE)

CDL3OUTSIDE

CDL3OUTSIDE([input_arrays])

Three Outside Up/Down (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDL3OUTSIDE)

CDL3STARSINSOUTH

CDL3STARSINSOUTH([input_arrays])

Three Stars In The South (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDL3STARSINSOUTH)

CDL3WHITESOLDIERS

CDL3WHITESOLDIERS([input_arrays])

Three Advancing White Soldiers (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDL3WHITESOLDIERS)

CDLABANDONEDBABY

CDLABANDONEDBABY([input_arrays], [penetration=0.3])

Abandoned Baby (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Parameters:
   penetration: 0.3

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

Params:
   * penetration (0.3)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLABANDONEDBABY)

CDLADVANCEBLOCK

CDLADVANCEBLOCK([input_arrays])

Advance Block (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLADVANCEBLOCK)

CDLBELTHOLD

CDLBELTHOLD([input_arrays])

Belt-hold (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLBELTHOLD)

CDLBREAKAWAY

CDLBREAKAWAY([input_arrays])

Breakaway (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLBREAKAWAY)

CDLCLOSINGMARUBOZU

CDLCLOSINGMARUBOZU([input_arrays])

Closing Marubozu (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLCLOSINGMARUBOZU)

CDLCONCEALBABYSWALL

CDLCONCEALBABYSWALL([input_arrays])

Concealing Baby Swallow (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLCONCEALBABYSWALL)

CDLCOUNTERATTACK

CDLCOUNTERATTACK([input_arrays])

Counterattack (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLCOUNTERATTACK)

CDLDARKCLOUDCOVER

CDLDARKCLOUDCOVER([input_arrays], [penetration=0.5])

Dark Cloud Cover (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Parameters:
   penetration: 0.5

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

Params:
   * penetration (0.5)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLDARKCLOUDCOVER)

CDLDOJI

CDLDOJI([input_arrays])

Doji (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLDOJI)

CDLDOJISTAR

CDLDOJISTAR([input_arrays])

Doji Star (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLDOJISTAR)

CDLDRAGONFLYDOJI

CDLDRAGONFLYDOJI([input_arrays])

Dragonfly Doji (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLDRAGONFLYDOJI)

CDLENGULFING

CDLENGULFING([input_arrays])

Engulfing Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLENGULFING)

CDLEVENINGDOJISTAR

CDLEVENINGDOJISTAR([input_arrays], [penetration=0.3])

Evening Doji Star (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Parameters:
   penetration: 0.3

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

Params:
   * penetration (0.3)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLEVENINGDOJISTAR)

CDLEVENINGSTAR

CDLEVENINGSTAR([input_arrays], [penetration=0.3])

Evening Star (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Parameters:
   penetration: 0.3

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

Params:
   * penetration (0.3)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLEVENINGSTAR)

CDLGAPSIDESIDEWHITE

CDLGAPSIDESIDEWHITE([input_arrays])

Up/Down-gap side-by-side white lines (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLGAPSIDESIDEWHITE)

CDLGRAVESTONEDOJI

CDLGRAVESTONEDOJI([input_arrays])

Gravestone Doji (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLGRAVESTONEDOJI)

CDLHAMMER

CDLHAMMER([input_arrays])

Hammer (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHAMMER)

CDLHANGINGMAN

CDLHANGINGMAN([input_arrays])

Hanging Man (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHANGINGMAN)

CDLHARAMI

CDLHARAMI([input_arrays])

Harami Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHARAMI)

CDLHARAMICROSS

CDLHARAMICROSS([input_arrays])

Harami Cross Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHARAMICROSS)

CDLHIGHWAVE

CDLHIGHWAVE([input_arrays])

High-Wave Candle (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHIGHWAVE)

CDLHIKKAKE

CDLHIKKAKE([input_arrays])

Hikkake Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHIKKAKE)

CDLHIKKAKEMOD

CDLHIKKAKEMOD([input_arrays])

Modified Hikkake Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHIKKAKEMOD)

CDLHOMINGPIGEON

CDLHOMINGPIGEON([input_arrays])

Homing Pigeon (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLHOMINGPIGEON)

CDLIDENTICAL3CROWS

CDLIDENTICAL3CROWS([input_arrays])

Identical Three Crows (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLIDENTICAL3CROWS)

CDLINNECK

CDLINNECK([input_arrays])

In-Neck Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLINNECK)

CDLINVERTEDHAMMER

CDLINVERTEDHAMMER([input_arrays])

Inverted Hammer (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLINVERTEDHAMMER)

CDLKICKING

CDLKICKING([input_arrays])

Kicking (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLKICKING)

CDLKICKINGBYLENGTH

CDLKICKINGBYLENGTH([input_arrays])

Kicking - bull/bear determined by the longer marubozu (Pattern
Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLKICKINGBYLENGTH)

CDLLADDERBOTTOM

CDLLADDERBOTTOM([input_arrays])

Ladder Bottom (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLLADDERBOTTOM)

CDLLONGLEGGEDDOJI

CDLLONGLEGGEDDOJI([input_arrays])

Long Legged Doji (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLLONGLEGGEDDOJI)

CDLLONGLINE

CDLLONGLINE([input_arrays])

Long Line Candle (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLLONGLINE)

CDLMARUBOZU

CDLMARUBOZU([input_arrays])

Marubozu (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLMARUBOZU)

CDLMATCHINGLOW

CDLMATCHINGLOW([input_arrays])

Matching Low (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLMATCHINGLOW)

CDLMATHOLD

CDLMATHOLD([input_arrays], [penetration=0.5])

Mat Hold (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Parameters:
   penetration: 0.5

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

Params:
   * penetration (0.5)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLMATHOLD)

CDLMORNINGDOJISTAR

CDLMORNINGDOJISTAR([input_arrays], [penetration=0.3])

Morning Doji Star (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Parameters:
   penetration: 0.3

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

Params:
   * penetration (0.3)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLMORNINGDOJISTAR)

CDLMORNINGSTAR

CDLMORNINGSTAR([input_arrays], [penetration=0.3])

Morning Star (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Parameters:
   penetration: 0.3

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

Params:
   * penetration (0.3)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLMORNINGSTAR)

CDLONNECK

CDLONNECK([input_arrays])

On-Neck Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLONNECK)

CDLPIERCING

CDLPIERCING([input_arrays])

Piercing Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLPIERCING)

CDLRICKSHAWMAN

CDLRICKSHAWMAN([input_arrays])

Rickshaw Man (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLRICKSHAWMAN)

CDLRISEFALL3METHODS

CDLRISEFALL3METHODS([input_arrays])

Rising/Falling Three Methods (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLRISEFALL3METHODS)

CDLSEPARATINGLINES

CDLSEPARATINGLINES([input_arrays])

Separating Lines (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLSEPARATINGLINES)

CDLSHOOTINGSTAR

CDLSHOOTINGSTAR([input_arrays])

Shooting Star (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLSHOOTINGSTAR)

CDLSHORTLINE

CDLSHORTLINE([input_arrays])

Short Line Candle (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLSHORTLINE)

CDLSPINNINGTOP

CDLSPINNINGTOP([input_arrays])

Spinning Top (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLSPINNINGTOP)

CDLSTALLEDPATTERN

CDLSTALLEDPATTERN([input_arrays])

Stalled Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLSTALLEDPATTERN)

CDLSTICKSANDWICH

CDLSTICKSANDWICH([input_arrays])

Stick Sandwich (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLSTICKSANDWICH)

CDLTAKURI

CDLTAKURI([input_arrays])

Takuri (Dragonfly Doji with very long lower shadow) (Pattern
Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLTAKURI)

CDLTASUKIGAP

CDLTASUKIGAP([input_arrays])

Tasuki Gap (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLTASUKIGAP)

CDLTHRUSTING

CDLTHRUSTING([input_arrays])

Thrusting Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLTHRUSTING)

CDLTRISTAR

CDLTRISTAR([input_arrays])

Tristar Pattern (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLTRISTAR)

CDLUNIQUE3RIVER

CDLUNIQUE3RIVER([input_arrays])

Unique 3 River (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLUNIQUE3RIVER)

CDLUPSIDEGAP2CROWS

CDLUPSIDEGAP2CROWS([input_arrays])

Upside Gap Two Crows (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLUPSIDEGAP2CROWS)

CDLXSIDEGAP3METHODS

CDLXSIDEGAP3METHODS([input_arrays])

Upside/Downside Gap Three Methods (Pattern Recognition)

Inputs:
   prices: ['open', 'high', 'low', 'close']

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

   * _candleplot

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (True)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - _plotskip (True)

   * _candleplot: - marker (d) - fillstyle (full) - markersize (7.0) -
     ls () - _name (CDLXSIDEGAP3METHODS)

CEIL

CEIL([input_arrays])

Vector Ceil (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

CMO

CMO([input_arrays], [timeperiod=14])

Chande Momentum Oscillator (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

CORREL

CORREL([input_arrays], [timeperiod=30])

Pearson's Correlation Coefficient (r) (Statistic Functions)

Inputs:
   price0: (any ndarray) price1: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

COS

COS([input_arrays])

Vector Trigonometric Cos (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

COSH

COSH([input_arrays])

Vector Trigonometric Cosh (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

DEMA

DEMA([input_arrays], [timeperiod=30])

Double Exponential Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

DIV

DIV([input_arrays])

Vector Arithmetic Div (Math Operators)

Inputs:
   price0: (any ndarray) price1: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

DX

DX([input_arrays], [timeperiod=14])

Directional Movement Index (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

EMA

EMA([input_arrays], [timeperiod=30])

Exponential Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

EXP

EXP([input_arrays])

Vector Arithmetic Exp (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

FLOOR

FLOOR([input_arrays])

Vector Floor (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

HT_DCPERIOD

HT_DCPERIOD([input_arrays])

Hilbert Transform - Dominant Cycle Period (Cycle Indicators)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

HT_DCPHASE

HT_DCPHASE([input_arrays])

Hilbert Transform - Dominant Cycle Phase (Cycle Indicators)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

HT_PHASOR

HT_PHASOR([input_arrays])

Hilbert Transform - Phasor Components (Cycle Indicators)

Inputs:
   price: (any ndarray)

Outputs:
   inphase quadrature

Lines:
   * inphase

   * quadrature

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * inphase: - ls (-)

   * quadrature: - ls (--)

HT_SINE

HT_SINE([input_arrays])

Hilbert Transform - SineWave (Cycle Indicators)

Inputs:
   price: (any ndarray)

Outputs:
   sine leadsine

Lines:
   * sine

   * leadsine

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * leadsine: - ls (--)

   * sine: - ls (-)

HT_TRENDLINE

HT_TRENDLINE([input_arrays])

Hilbert Transform - Instantaneous Trendline (Overlap Studies)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

HT_TRENDMODE

HT_TRENDMODE([input_arrays])

Hilbert Transform - Trend vs Cycle Mode (Cycle Indicators)

Inputs:
   price: (any ndarray)

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - ls (-)

KAMA

KAMA([input_arrays], [timeperiod=30])

Kaufman Adaptive Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

LINEARREG

LINEARREG([input_arrays], [timeperiod=14])

Linear Regression (Statistic Functions)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

LINEARREG_ANGLE

LINEARREG_ANGLE([input_arrays], [timeperiod=14])

Linear Regression Angle (Statistic Functions)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

LINEARREG_INTERCEPT

LINEARREG_INTERCEPT([input_arrays], [timeperiod=14])

Linear Regression Intercept (Statistic Functions)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

LINEARREG_SLOPE

LINEARREG_SLOPE([input_arrays], [timeperiod=14])

Linear Regression Slope (Statistic Functions)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

LN

LN([input_arrays])

Vector Log Natural (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

LOG10

LOG10([input_arrays])

Vector Log10 (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MA

MA([input_arrays], [timeperiod=30], [matype=0])

Moving average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30 matype: 0 (Simple Moving Average)

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

   * matype (0)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MACD

MACD([input_arrays], [fastperiod=12], [slowperiod=26],
[signalperiod=9])

Moving Average Convergence/Divergence (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   fastperiod: 12 slowperiod: 26 signalperiod: 9

Outputs:
   macd macdsignal macdhist

Lines:
   * macd

   * macdsignal

   * macdhist

Params:
   * fastperiod (12)

   * slowperiod (26)

   * signalperiod (9)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * macdsignal: - ls (--)

   * macd: - ls (-)

   * macdhist: - _method (bar)

MACDEXT

MACDEXT([input_arrays], [fastperiod=12], [fastmatype=0],
[slowperiod=26], [slowmatype=0], [signalperiod=9], [signalmatype=0])

MACD with controllable MA type (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   fastperiod: 12 fastmatype: 0 slowperiod: 26 slowmatype: 0
   signalperiod: 9 signalmatype: 0

Outputs:
   macd macdsignal macdhist

Lines:
   * macd

   * macdsignal

   * macdhist

Params:
   * fastperiod (12)

   * fastmatype (0)

   * slowperiod (26)

   * slowmatype (0)

   * signalperiod (9)

   * signalmatype (0)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * macdsignal: - ls (--)

   * macd: - ls (-)

   * macdhist: - _method (bar)

MACDFIX

MACDFIX([input_arrays], [signalperiod=9])

Moving Average Convergence/Divergence Fix 12/26 (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   signalperiod: 9

Outputs:
   macd macdsignal macdhist

Lines:
   * macd

   * macdsignal

   * macdhist

Params:
   * signalperiod (9)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * macdsignal: - ls (--)

   * macd: - ls (-)

   * macdhist: - _method (bar)

MAMA

MAMA([input_arrays], [fastlimit=0.5], [slowlimit=0.05])

MESA Adaptive Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   fastlimit: 0.5 slowlimit: 0.05

Outputs:
   mama fama

Lines:
   * mama

   * fama

Params:
   * fastlimit (0.5)

   * slowlimit (0.05)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * mama: - ls (-)

   * fama: - ls (--)

MAVP

MAVP([input_arrays], [minperiod=2], [maxperiod=30], [matype=0])

Moving average with variable period (Overlap Studies)

Inputs:
   price: (any ndarray) periods: (any ndarray)

Parameters:
   minperiod: 2 maxperiod: 30 matype: 0 (Simple Moving Average)

Outputs:
   real

Lines:
   * real

Params:
   * minperiod (2)

   * maxperiod (30)

   * matype (0)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MAX

MAX([input_arrays], [timeperiod=30])

Highest value over a specified period (Math Operators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MAXINDEX

MAXINDEX([input_arrays], [timeperiod=30])

Index of highest value over a specified period (Math Operators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - ls (-)

MEDPRICE

MEDPRICE([input_arrays])

Median Price (Price Transform)

Inputs:
   prices: ['high', 'low']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MFI

MFI([input_arrays], [timeperiod=14])

Money Flow Index (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close', 'volume']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MIDPOINT

MIDPOINT([input_arrays], [timeperiod=14])

MidPoint over period (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MIDPRICE

MIDPRICE([input_arrays], [timeperiod=14])

Midpoint Price over period (Overlap Studies)

Inputs:
   prices: ['high', 'low']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MIN

MIN([input_arrays], [timeperiod=30])

Lowest value over a specified period (Math Operators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MININDEX

MININDEX([input_arrays], [timeperiod=30])

Index of lowest value over a specified period (Math Operators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   integer (values are -100, 0 or 100)

Lines:
   * integer

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * integer: - ls (-)

MINMAX

MINMAX([input_arrays], [timeperiod=30])

Lowest and highest values over a specified period (Math Operators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   min max

Lines:
   * min

   * max

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * max: - ls (-)

   * min: - ls (-)

MINMAXINDEX

MINMAXINDEX([input_arrays], [timeperiod=30])

Indexes of lowest and highest values over a specified period (Math
Operators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   minidx maxidx

Lines:
   * minidx

   * maxidx

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * maxidx: - ls (-)

   * minidx: - ls (-)

MINUS_DI

MINUS_DI([input_arrays], [timeperiod=14])

Minus Directional Indicator (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MINUS_DM

MINUS_DM([input_arrays], [timeperiod=14])

Minus Directional Movement (Momentum Indicators)

Inputs:
   prices: ['high', 'low']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MOM

MOM([input_arrays], [timeperiod=10])

Momentum (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 10

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (10)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

MULT

MULT([input_arrays])

Vector Arithmetic Mult (Math Operators)

Inputs:
   price0: (any ndarray) price1: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

NATR

NATR([input_arrays], [timeperiod=14])

Normalized Average True Range (Volatility Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

OBV

OBV([input_arrays])

On Balance Volume (Volume Indicators)

Inputs:
   price: (any ndarray) prices: ['volume']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

PLUS_DI

PLUS_DI([input_arrays], [timeperiod=14])

Plus Directional Indicator (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

PLUS_DM

PLUS_DM([input_arrays], [timeperiod=14])

Plus Directional Movement (Momentum Indicators)

Inputs:
   prices: ['high', 'low']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

PPO

PPO([input_arrays], [fastperiod=12], [slowperiod=26], [matype=0])

Percentage Price Oscillator (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   fastperiod: 12 slowperiod: 26 matype: 0 (Simple Moving Average)

Outputs:
   real

Lines:
   * real

Params:
   * fastperiod (12)

   * slowperiod (26)

   * matype (0)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ROC

ROC([input_arrays], [timeperiod=10])

Rate of change : ((price/prevPrice)-1)*100 (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 10

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (10)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ROCP

ROCP([input_arrays], [timeperiod=10])

Rate of change Percentage: (price-prevPrice)/prevPrice (Momentum
Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 10

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (10)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ROCR

ROCR([input_arrays], [timeperiod=10])

Rate of change ratio: (price/prevPrice) (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 10

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (10)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ROCR100

ROCR100([input_arrays], [timeperiod=10])

Rate of change ratio 100 scale: (price/prevPrice)*100 (Momentum
Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 10

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (10)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

RSI

RSI([input_arrays], [timeperiod=14])

Relative Strength Index (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

SAR

SAR([input_arrays], [acceleration=0.02], [maximum=0.2])

Parabolic SAR (Overlap Studies)

Inputs:
   prices: ['high', 'low']

Parameters:
   acceleration: 0.02 maximum: 0.2

Outputs:
   real

Lines:
   * real

Params:
   * acceleration (0.02)

   * maximum (0.2)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

SAREXT

SAREXT([input_arrays], [startvalue=0], [offsetonreverse=0],
[accelerationinitlong=0.02], [accelerationlong=0.02],
[accelerationmaxlong=0.2], [accelerationinitshort=0.02],
[accelerationshort=0.02], [accelerationmaxshort=0.2])

Parabolic SAR - Extended (Overlap Studies)

Inputs:
   prices: ['high', 'low']

Parameters:
   startvalue: 0 offsetonreverse: 0 accelerationinitlong: 0.02
   accelerationlong: 0.02 accelerationmaxlong: 0.2
   accelerationinitshort: 0.02 accelerationshort: 0.02
   accelerationmaxshort: 0.2

Outputs:
   real

Lines:
   * real

Params:
   * startvalue (0)

   * offsetonreverse (0)

   * accelerationinitlong (0.02)

   * accelerationlong (0.02)

   * accelerationmaxlong (0.2)

   * accelerationinitshort (0.02)

   * accelerationshort (0.02)

   * accelerationmaxshort (0.2)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

SIN

SIN([input_arrays])

Vector Trigonometric Sin (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

SINH

SINH([input_arrays])

Vector Trigonometric Sinh (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

SMA

SMA([input_arrays], [timeperiod=30])

Simple Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

SQRT

SQRT([input_arrays])

Vector Square Root (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

STDDEV

STDDEV([input_arrays], [timeperiod=5], [nbdev=1])

Standard Deviation (Statistic Functions)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 5 nbdev: 1

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (5)

   * nbdev (1)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

STOCH

STOCH([input_arrays], [fastk_period=5], [slowk_period=3],
[slowk_matype=0], [slowd_period=3], [slowd_matype=0])

Stochastic (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   fastk_period: 5 slowk_period: 3 slowk_matype: 0 slowd_period: 3
   slowd_matype: 0

Outputs:
   slowk slowd

Lines:
   * slowk

   * slowd

Params:
   * fastk_period (5)

   * slowk_period (3)

   * slowk_matype (0)

   * slowd_period (3)

   * slowd_matype (0)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * slowk: - ls (--)

   * slowd: - ls (--)

STOCHF

STOCHF([input_arrays], [fastk_period=5], [fastd_period=3],
[fastd_matype=0])

Stochastic Fast (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   fastk_period: 5 fastd_period: 3 fastd_matype: 0

Outputs:
   fastk fastd

Lines:
   * fastk

   * fastd

Params:
   * fastk_period (5)

   * fastd_period (3)

   * fastd_matype (0)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * fastk: - ls (-)

   * fastd: - ls (-)

STOCHRSI

STOCHRSI([input_arrays], [timeperiod=14], [fastk_period=5],
[fastd_period=3], [fastd_matype=0])

Stochastic Relative Strength Index (Momentum Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14 fastk_period: 5 fastd_period: 3 fastd_matype: 0

Outputs:
   fastk fastd

Lines:
   * fastk

   * fastd

Params:
   * timeperiod (14)

   * fastk_period (5)

   * fastd_period (3)

   * fastd_matype (0)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * fastk: - ls (-)

   * fastd: - ls (-)

SUB

SUB([input_arrays])

Vector Arithmetic Substraction (Math Operators)

Inputs:
   price0: (any ndarray) price1: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

SUM

SUM([input_arrays], [timeperiod=30])

Summation (Math Operators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

T3

T3([input_arrays], [timeperiod=5], [vfactor=0.7])

Triple Exponential Moving Average (T3) (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 5 vfactor: 0.7

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (5)

   * vfactor (0.7)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TAN

TAN([input_arrays])

Vector Trigonometric Tan (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TANH

TANH([input_arrays])

Vector Trigonometric Tanh (Math Transform)

Inputs:
   price: (any ndarray)

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TEMA

TEMA([input_arrays], [timeperiod=30])

Triple Exponential Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TRANGE

TRANGE([input_arrays])

True Range (Volatility Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TRIMA

TRIMA([input_arrays], [timeperiod=30])

Triangular Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TRIX

TRIX([input_arrays], [timeperiod=30])

1-day Rate-Of-Change (ROC) of a Triple Smooth EMA (Momentum
Indicators)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TSF

TSF([input_arrays], [timeperiod=14])

Time Series Forecast (Statistic Functions)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

TYPPRICE

TYPPRICE([input_arrays])

Typical Price (Price Transform)

Inputs:
   prices: ['high', 'low', 'close']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

ULTOSC

ULTOSC([input_arrays], [timeperiod1=7], [timeperiod2=14],
[timeperiod3=28])

Ultimate Oscillator (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod1: 7 timeperiod2: 14 timeperiod3: 28

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod1 (7)

   * timeperiod2 (14)

   * timeperiod3 (28)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

VAR

VAR([input_arrays], [timeperiod=5], [nbdev=1])

Variance (Statistic Functions)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 5 nbdev: 1

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (5)

   * nbdev (1)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

WCLPRICE

WCLPRICE([input_arrays])

Weighted Close Price (Price Transform)

Inputs:
   prices: ['high', 'low', 'close']

Outputs:
   real

Lines:
   * real

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

WILLR

WILLR([input_arrays], [timeperiod=14])

Williams' %R (Momentum Indicators)

Inputs:
   prices: ['high', 'low', 'close']

Parameters:
   timeperiod: 14

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (14)

PlotInfo:
   * subplot (True)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

WMA

WMA([input_arrays], [timeperiod=30])

Weighted Moving Average (Overlap Studies)

Inputs:
   price: (any ndarray)

Parameters:
   timeperiod: 30

Outputs:
   real

Lines:
   * real

Params:
   * timeperiod (30)

PlotInfo:
   * subplot (False)

   * plot (True)

   * plotskip (False)

   * plotname ()

   * plotforce (False)

   * plotyhlines ([])

   * plothlines ([])

   * plotabove (False)

   * plotymargin (0.0)

   * plotlinelabels (False)

   * plotmaster (None)

   * plotyticks ([])

PlotLines:
   * real: - ls (-)

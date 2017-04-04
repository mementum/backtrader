Data Feeds
##########

``backtrader`` comes with a set of Data Feed parsers (at the time of writing all
CSV Based) to let you load data from different sources.

  - Yahoo (online or already saved to a file)

  - VisualChart (see `www.visualchart.com <http://www.visualchart.com>`_

  - Backtrader CSV (own cooked format for testing)

  - Generic CSV support

From the :ref:`Quickstart` guide it should be clear that you add data feeds to a
``Cerebro`` instance. The data feeds will later be available to the different
strategies in:

  - An array `self.datas` (insertion order)

  - Alias to the array objects:

    - self.data and self.data0 point to the first element
    - self.dataX points to elements with index X in the array

A quick reminder as to how the insertion works::

  import backtrader as bt
  import backtrader.feeds as btfeeds

  data = btfeeds.YahooFinanceCSVData(dataname='wheremydatacsvis.csv')

  cerebro = bt.Cerebro()

  cerebro.adddata(data)  # a 'name' parameter can be passed for plotting purposes


Data Feeds Common parameters
****************************

This data feed can download data directly from Yahoo and feed into the system.

Parameters:

  - ``dataname`` (default: None) MUST BE PROVIDED

    The meaning varies with the data feed type (file location, ticker, ...)

  - ``name`` (default: '')

    Meant for decorative purposes in plotting. If not specified it may be
    derived from ``dataname`` (example: last part of a file path)

  - ``fromdate`` (default: mindate)

    Python datetime object indicating that any datetime prior to this should be
    ignored

  - ``todate`` (default: maxdate)

    Python datetime object indicating that any datetime posterior to this should
    be ignored

  - ``timeframe`` (default: TimeFrame.Days)

    Potential values: ``Ticks``, ``Seconds``, ``Minutes``, ``Days``, ``Weeks``,
    ``Months`` and ``Years``

  - ``compression`` (default: 1)

    Number of actual bars per bar. Informative. Only effective in Data
    Resampling/Replaying.

  - ``sessionstart`` (default: None)

    Indication of session starting time for the data. May be used by classes for
    purposes like resampling

  - ``sessionend`` (default: None)

    Indication of session ending time for the data. May be used by classes for
    purposes like resampling


CSV Data Feeds Common parameters
********************************

Parameters (additional to the common ones):

  - ``headers`` (default: True)

    Indicates if the passed data has an initial headers row

  - ``separator`` (default: ",")

    Separator to take into account to tokenize each of the CSV rows


.. _generic-csv-datafeed:

GenericCSVData
**************

This class exposes a generic interface allowing parsing mostly every CSV file
format out there.

Parses a CSV file according to the order and field presence defined by the parameters

Specific parameters (or specific meaning):

  - ``dataname``

    The filename to parse or a file-like object

  - ``datetime`` (default: 0) column containing the date (or datetime) field

  - ``time`` (default: -1) column containing the time field if separate from the
    datetime field (-1 indicates it's not present)

  - ``open`` (default: 1) , ``high`` (default: 2), ``low`` (default: 3),
    ``close`` (default: 4), ``volume`` (default: 5), ``openinterest``
    (default: 6)

    Index of the columns containing the corresponding fields

    If a negative value is passed (example: -1) it indicates the field is not
    present in the CSV data

  - ``nullvalue`` (default: float('NaN'))

    Value that will be used if a value which should be there is missing (the CSV
    field is empty)

  - ``dtformat`` (default: %Y-%m-%d %H:%M:%S)

    Format used to parse the datetime CSV field

  - ``tmformat`` (default: %H:%M:%S)

    Format used to parse the time CSV field if "present" (the default for the
    "time" CSV field is not to be present)

An example usage covering the following requirements:

  - Limit input to year 2000
  - HLOC order rather than OHLC
  - Missing values to be replaced with zero (0.0)
  - Daily bars are provided and datetime is just the day with format YYYY-MM-DD
  - No ``openinterest`` column is present

The code::

  import datetime
  import backtrader as bt
  import backtrader.feeds as btfeeds

  ...
  ...

  data = btfeeds.GenericCSVData(
      dataname='mydata.csv',

      fromdate=datetime.datetime(2000, 1, 1),
      todate=datetime.datetime(2000, 12, 31),

      nullvalue=0.0,

      dtformat=('%Y-%m-%d'),

      datetime=0,
      high=1,
      low=2,
      open=3,
      close=4,
      volume=5,
      openinterest=-1
  )

  ...

Slightly modified requirements:

  - Limit input to year 2000
  - HLOC order rather than OHLC
  - Missing values to be replaced with zero (0.0)
  - Intraday bars are provided, with separate date and time columns
    - Date has format YYYY-MM-DD
    - Time has format HH.MM.SS (instead of the usual HH:MM:SS)
  - No ``openinterest`` column is present

The code::

  import datetime
  import backtrader as bt
  import backtrader.feeds as btfeed

  ...
  ...

  data = btfeeds.GenericCSVData(
      dataname='mydata.csv',

      fromdate=datetime.datetime(2000, 1, 1),
      todate=datetime.datetime(2000, 12, 31),

      nullvalue=0.0,

      dtformat=('%Y-%m-%d'),
      tmformat=('%H.%M.%S'),

      datetime=0,
      time=1,
      high=2,
      low=3,
      open=4,
      close=5,
      volume=6,
      openinterest=-1
  )


This can also be made *permanent* with subclassing::

  import datetime
  import backtrader.feeds as btfeed

  class MyHLOC(btfreeds.GenericCSVData):

    params = (
      ('fromdate', datetime.datetime(2000, 1, 1)),
      ('todate', datetime.datetime(2000, 12, 31)),
      ('nullvalue', 0.0),
      ('dtformat', ('%Y-%m-%d')),
      ('tmformat', ('%H.%M.%S')),

      ('datetime', 0),
      ('time', 1),
      ('high', 2),
      ('low', 3),
      ('open', 4),
      ('close', 5),
      ('volume', 6),
      ('openinterest', -1)
  )

This new class can be reused now by just providing the ``dataname``::

  data = btfeeds.MyHLOC(dataname='mydata.csv')

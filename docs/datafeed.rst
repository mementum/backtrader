Data Feeds
##########

``backtrader`` comes with a set of Data Feed parsers (at the time of writing all
CSV Based) to let you load data from different sources.

  - Yahoo (online or already saved to a file)

  - VisualChart (see `www.visualchart.com <http://www.visualchart.com>`_

  - Backtrader CSV (own cooked format for testing)

  - Generic CSV support

From the `Quickstart`_ guide it should be clear that you add data feeds to a
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


CSV Data Feeds Common parameters
********************************

This data feed can download data directly from Yahoo and feed into the system.

Parameters:

  - ``dataname``

    The meaning varies with the data feed type (file location, ticker, ...)

  - ``fromdate`` (default: mindate)

    Python datetime object indicating that any datetime prior to this should be
    ignored

  - ``todate`` (default: maxdate)

    Python datetime object indicating that any datetime posterior to this should
    be ignored

  - ``headers`` (default: True)

    Indicates if the passed data has an initial headers row

  - ``separator`` (default: ",")

    Separator to take into account to tokenize each of the CSV rows


The actual CSV Data Feeds
*************************

YahooFinanceData
================

Executes a direct download of data from Yahoo servers for the given time range.

Specific parameters (or specific meaning):

  - ``dataname``

    The ticker to download ('YHOO' for Yahoo own stock quotes)

  - ``baseurl`` (default: 'http://ichart.yahoo.com/table.csv?')

    The server url. Someone might decide to open a Yahoo compatible service in the
    future.

  - ``period`` (default: 'd' for daily)

    The timeframe to download data in. Pass 'w' for weekly and 'm' for monthly.

  - ``buffered`` (default: True)

    If True the entire socket connection wil be buffered locally before parsing
    starts.

  - ``reverse`` (default: True)

    Yahoo returns the data with last dates first (against all industry
    standards) and it must be reversed for it to work. Should this Yahoo
    standard change, the parameter is available.

  - ``adjclose`` (default: True)

    Whether to use the dividend/split adjusted close and adjust all values
    according to it.

Example to get Yahoo quotes for 1999::

  ...
  import backtrader.feeds as btfeeds

  ...
  data = btfeeds.YahooFinanceData(
      dataname='YHOO',
      fromdate=datetime.datetime(1999, 1, 1),
      todate=datetime.datetime(1999, 12, 31)
  )

  ...

YahooFinanceCSVData
===================

Parses pre-downloaded Yahoo CSV Data Feeds (or locally generated if they comply
to the Yahoo format)

Specific parameters (or specific meaning):

  - ``dataname``

    The filename to parse or a file-like object

  - ``reverse`` (default: False)

    It is assumed that locally stored files have already been reversed during
    the download process

  - ``adjclose`` (default: True)

    Whether to use the dividend/split adjusted close and adjust all values
    according to it.

Example to get Yahoo quotes for 1999::

  ...
  import backtrader.feeds as btfeeds

  ...
  data = btfeeds.YahooFinanceData(
      dataname='yhoo-1995-2015-daily.csv',
      fromdate=datetime.datetime(1999, 1, 1),
      todate=datetime.datetime(1999, 12, 31)
  )

  ...

VchartCSVData
=============

Parses a `VisualChart <http://www.visualchart.com>`_ CSV exported file.

Specific parameters (or specific meaning):

  - ``dataname``

    The filename to parse or a file-like object

Example::

  ...
  import backtrader.feeds as btfeeds

  ...
  data = btfeeds.VChartCSVData(
      dataname='vchart-nvda-1995-2015-daily.txt',
      fromdate=datetime.datetime(1999, 1, 1),
      todate=datetime.datetime(1999, 12, 31)
  )

  ...


BacktraderCSVData
=================

Parses a self-defined CSV Data used for testing.

Specific parameters (or specific meaning):

  - ``dataname``

    The filename to parse or a file-like object

Example::

  ...
  import backtrader.feeds as btfeeds

  ...
  data = btfeeds.BacktraderCSVData(
      dataname='bt-sample-1995-2015-daily.txt',
      fromdate=datetime.datetime(1999, 1, 1),
      todate=datetime.datetime(1999, 12, 31)
  )

  ...


GenericCSVData
==============

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

  data = btfeed.GenericCSVData(
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

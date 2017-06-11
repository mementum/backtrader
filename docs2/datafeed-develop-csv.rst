.. _csv-data-feed-development:

CSV Data Feed Development
#########################

``backtrader`` already offers a Generic CSV Data feed and some specific CSV Data
Feeds. Summarizing:

  - GenericCSVData
  - VisualChartCSVData
  - YahooFinanceData (for online downloads)
  - YahooFinanceCSVData (for already downloaded data)
  - BacktraderCSVData (in-house ... for testing purposed, but can be used)

But even with that, the end user may wish to develop support for a specific CSV
Data Feed.

The usual motto would be: "It's easier said than done". Actually the structure
is meant to make it easy.

Steps:

  - Inherit from ``backtrader.CSVDataBase``

  - Define any ``params`` if needed

  - Do any initialization in the ``start`` method

  - Do any clean-up in the ``stop`` method

  - Define a ``_loadline`` method where the actual work happens

    This method receives a single argument: linetokens.

    As the name suggests this contains the tokens after the current line has
    been splitten according to the ``separator`` parameter (inherited from the
    base class)

    If after doing its work there is new data ... fill up the corresponding
    lines and return ``True``

    If nothing is available and therefore the parsing has come to an end: return
    ``False``

    Returning ``False`` may not even be needed if the behind the scenes code
    which is reading the file lines finds out there are no more lines to parse.

Things which are already taken into account:

  - Opening the file (or receiving a file-like object)
  - Skipping the headers row if indicated as present
  - Reading the lines
  - Tokenizing the lines
  - Preloading support (to load the entire data feed at once in memory)

Usually an example is worth a thousand requirement descriptions. Let's use a
simplified version of the in-house defined CSV parsing code from
``BacktraderCSVData``. This one needs no initialization or clean-up (this could
be opening a socket and closing it later, for example).

.. note::

   ``backtrader`` data feeds contain the usual industry standard feeds, which
   are the ones to be filled. Namely:

     - datetime
     - open
     - high
     - low
     - close
     - volume
     - openinterest

   If your strategy/algorithm or simple data perusal only needs, for example the
   closing prices you can leave the others untouched (each iteration fills them
   automatically with a float('NaN') value before the end user code has a chance
   to do anything.

In this example only a daily format is supported::

  import itertools
  ...
  import backtrader as bt

  class MyCSVData(bt.CSVDataBase):

      def start(self):
          # Nothing to do for this data feed type
          pass

      def stop(self):
          # Nothing to do for this data feed type
          pass

      def _loadline(self, linetokens):
          i = itertools.count(0)

          dttxt = linetokens[next(i)]
          # Format is YYYY-MM-DD
          y = int(dttxt[0:4])
          m = int(dttxt[5:7])
          d = int(dttxt[8:10])

          dt = datetime.datetime(y, m, d)
          dtnum = date2num(dt)

          self.lines.datetime[0] = dtnum
          self.lines.open[0] = float(linetokens[next(i)])
          self.lines.high[0] = float(linetokens[next(i)])
          self.lines.low[0] = float(linetokens[next(i)])
          self.lines.close[0] = float(linetokens[next(i)])
          self.lines.volume[0] = float(linetokens[next(i)])
          self.lines.openinterest[0] = float(linetokens[next(i)])

          return True

The code expects all fields to be in place and be convertible to floats, except
for the datetime which has a fixed YYYY-MM-DD format and can be parsed without
using ``datetime.datetime.strptime``.

More complex needs can be covered by adding just a few lines of code to account
for null values, date format parsing. The ``GenericCSVData`` does that.

Caveat Emptor
=============

Using the ``GenericCSVData`` existing feed and inheritance a lot can be
acomplished in order to support formats.

Let's add support for `Sierra Chart <www.sierrachart.com>`_ daily format (which
is always stored in CSV format).

Definition (by looking into one of the **'.dly'** data files:

  - **Fields**: Date, Open, High, Low, Close, Volume, OpenInterest

    The industry standard ones and the ones already supported by
    ``GenericCSVData`` in the same order (which is also industry standard)

  - **Separator**: ,

  - **Date Format**: YYYY/MM/DD

A parser for those files::

  class SierraChartCSVData(backtrader.feeds.GenericCSVData):

      params = (('dtformat', '%Y/%m/%d'),)

The ``params`` definition simply redefines one of the existing parameters in the
base class. In this case just the formatting string for dates needs a change.

Et voilá ... the parser for **Sierra Chart** is finished.

Here below the parameters definition of ``GenericCSVData`` as a reminder::

  class GenericCSVData(feed.CSVDataBase):
      params = (
          ('nullvalue', float('NaN')),
          ('dtformat', '%Y-%m-%d %H:%M:%S'),
          ('tmformat', '%H:%M:%S'),

          ('datetime', 0),
          ('time', -1),
          ('open', 1),
          ('high', 2),
          ('low', 3),
          ('close', 4),
          ('volume', 5),
          ('openinterest', 6),
      )

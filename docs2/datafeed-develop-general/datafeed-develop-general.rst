
Binary Datafeed Development
###########################

.. note::

   The binary file used in the examples ``goog.fd`` belongs to VisualChart and
   cannot be distributed with ``backtrader``.

   `VisualChart <http://www.visualchart.com>`_ can be downloaded free of charge for
   those interested in directly using the binary files.

CSV Data feed development has shown how to add new CSV based data
feeds. The existing base class `CSVDataBase` provides the framework
taking most of the work off the subclasses which in most cases can
simply do::

  def _loadline(self, linetokens):

    # parse the linetokens here and put them in self.lines.close,
    # self.lines.high, etc

    return True # if data was parsed, else ... return False

The base class takes care of the parameters, initialization, opening of files,
reading lines, splitting the lines in tokens and additional things like skipping
lines which don't fit into the date range (``fromdate``, ``todate``) which the
end user may have defined.

Developing a non-CSV datafeed follows the same pattern without going down to the
already splitted line tokens.

Things to do:

  - Derive from backtrader.feed.DataBase

  - Add any parameters you may need

  - Should initialization be needed, override ``__init__(self)`` and/or ``start(self)``

  - Should any clean-up code be needed, override ``stop(self)``

  - The work happens inside the method which MUST always be overriden: ``_load(self)``

Let's the parameters already provided by ``backtrader.feed.DataBase``::

  from backtrader.utils.py3 import with_metaclass

  ...
  ...

  class DataBase(with_metaclass(MetaDataBase, dataseries.OHLCDateTime)):

      params = (('dataname', None),
          ('fromdate', datetime.datetime.min),
	  ('todate', datetime.datetime.max),
	  ('name', ''),
	  ('compression', 1),
	  ('timeframe', TimeFrame.Days),
	  ('sessionend', None))

Having the following meanings:

  - ``dataname`` is what allows the data feed to identify how to fetch the
    data. In the case of the ``CSVDataBase`` this parameter is meant to be a
    path to a file or already a file-like object.

  - ``fromdate`` and ``todate`` define the date range which will be passed to
    strategies. Any value provided by the feed outside of this range will be
    ignored

  - ``name`` is cosmetic for plotting purposes

  - ``timeframe`` indicates the temporal working reference

    Potential values: ``Ticks``, ``Seconds``, ``Minutes``, ``Days``, ``Weeks``,
    ``Months`` and ``Years``

  - ``compression`` (default: 1)

    Number of actual bars per bar. Informative. Only effective in Data
    Resampling/Replaying.

  - ``compression``

  - ``sessionend`` if passed (a datetime.time object) will be added to the
    datafeed ``datetime`` line which allows identifying the end of the session

Sample binary datafeed
======================

``backtrader`` already defines a CSV datafeed (``VChartCSVData``) for the
exports of `VisualChart <http://www.visualchart.com>`_, but it is also possible to
directly read the binary data files.

Let's do it (full data feed code can be found at the bottom)

Initialization
--------------

The binary VisualChart data files can contain either daily (.fd extension) or
intraday data (.min extension). Here the parameter ``timeframe``
will be used to distinguish which type of file is being read.

During ``__init__`` constants which differ for each type are set up.

.. literalinclude:: ./vchart.py
   :language: python
   :lines: 33-46

Start
-----

The Datafeed will be *started* when backtesting commences (it can actually be
started several times during optimizations)

In the ``start`` method the binary file is open unless a file-like object has
been passed.

.. literalinclude:: ./vchart.py
   :language: python
   :lines: 47-56

Stop
----

Called when backtesting is finished.

If a file was open, it will be closed

.. literalinclude:: ./vchart.py
   :language: python
   :lines: 57-62

Actual Loading
--------------

The actual work is done in ``_load``. Called to load the next set of data, in
this case the next : datetime, open, high, low, close, volume, openinterest. In
``backtrader`` the "actual" moment corresponds to index 0.

A number of bytes will be read from the open file (determined by the constants
set up during ``__init__``), parsed with the ``struct`` module, further
processed if needed (like with divmod operations for date and time) and stored
in the ``lines`` of the data feed: datetime, open, high, low, close, volume,
openinterest.

If no data can be read from the file it is assumed that the End Of File (EOF)
has been reached

  - ``False`` is returned to indicate the fact no more data is available

Else if data has been loaded and parsed:

  - ``True`` is returned to indicate the loading of the data set was a success

.. literalinclude:: ./vchart.py
   :language: python
   :lines: 63-104


Other Binary Formats
====================

The same model can be applied to any other binary source:

  - Database

  - Hierarchical data storage

  - Online source

The steps again:

  - ``__init__`` -> Any init code for the instance, only once

  - ``start`` -> start of backtesting (one or more times if optimization will be
    run)

    This would for example open the connection to the database or a socket to an
    online service

  - ``stop`` -> clean-up like closing the database connection or open sockets

  - ``_load`` -> query the database or online source for the next set of data
    and load it into the ``lines`` of the object. The standard fields being:
    datetime, open, high, low, close, volume, openinterest

VChartData Test
===============

The ``VCharData`` loading data from a local ".fd" file for Google for the
year 2006.

It's only about loading the data, so not even a subclass of ``Strategy`` is
needed.

.. literalinclude:: ./vchart-test.py
   :language: python
   :lines: 21-

.. thumbnail:: ./vchart-goog-2006.png

VChartData Full Code
====================

.. literalinclude:: ./vchart.py
   :language: python
   :lines: 21-

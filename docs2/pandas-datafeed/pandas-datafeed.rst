Pandas DataFeed Example
#######################

.. note::

   ``pandas`` and its dependencies have to be installed

Supporting `Pandas <http://pandas.pydata.org>`_ Dataframes seems to be of concern to
lots of people, who rely on the already available parsing code for different
data sources (including CSV) and other functionalities offered by Pandas.

The important declarations for the Datafeed.

.. literalinclude:: ./pfeed.py
   :language: python
   :lines: 30-56

The above excerpt from the ``PandasData`` class shows the keys:

  - The ``dataname`` parameter to the class during instantiation holds the
    Pandas Dataframe

    This parameter is inherited from the base class ``feed.DataBase``

  - The new parameters have the names of the regular fields in the
    ``DataSeries`` and follow these conventions

    - ``datetime`` (default: None)

      - None : datetime is the "index" in the Pandas Dataframe
      - -1 : autodetect position or case-wise equal name
      - >= 0 : numeric index to the colum in the pandas dataframe
      - string : column name (as index) in the pandas dataframe

    - ``open``, ``high``, ``low``, ``high``, ``close``, ``volume``,
      ``openinterest`` (default: -1 for all of them)

      - None : column not present
      - -1 : autodetect position or case-wise equal name
      - >= 0 : numeric index to the colum in the pandas dataframe
      - string : column name (as index) in the pandas dataframe

A small sample should be able to load the standar 2006 sample, having been
parsed by ``Pandas``, rather than directly by ``backtrader``

Running the sample to use the exiting "headers" in the CSV data::

  $ ./panda-test.py
  --------------------------------------------------
                 Open     High      Low    Close  Volume  OpenInterest
  Date
  2006-01-02  3578.73  3605.95  3578.73  3604.33       0             0
  2006-01-03  3604.08  3638.42  3601.84  3614.34       0             0
  2006-01-04  3615.23  3652.46  3615.23  3652.46       0             0

The same but telling the script to skip the headers::

  $ ./panda-test.py --noheaders
  --------------------------------------------------
                    1        2        3        4  5  6
  0
  2006-01-02  3578.73  3605.95  3578.73  3604.33  0  0
  2006-01-03  3604.08  3638.42  3601.84  3614.34  0  0
  2006-01-04  3615.23  3652.46  3615.23  3652.46  0  0

The 2nd run is using tells ``pandas.read_csv``:

  - To skip the first input row (``skiprows`` keyword argument set to 1)

  - Not to look for a headers row (``header`` keyword argument set to None)

The ``backtrader`` support for Pandas tries to automatically detect if column
names have been used or else numeric indices and acts accordingly, trying to
offer a best match.

The following chart is the tribute to success. The Pandas Dataframe has been
correctly loaded (in both cases)

.. thumbnail:: ./pandas-headers.png

The sample code for the test.

.. literalinclude:: ./panda-test.py
   :language: python
   :lines: 21-

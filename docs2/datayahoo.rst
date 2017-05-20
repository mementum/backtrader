Yahoo Data Feed Notes
#####################

In May 2017 Yahoo discontinued the existing API for historical data downloads
in *csv* format.

A new API (here named ``v7``) was quickly *standardized* and has been
implemented.

This also brought a change to the actual CSV download format.

Using the v7 API/format
***********************

Starting with version ``1.9.49.116`` this is the default behavior. Choose
simply from

  - ``YahooFinanceData`` for online downloads
  - ``YahooFinanceCSVData`` for offline downloaded files


Using the legacy API/format
***************************

To use the old API/format

  1. Instantiate the online Yahoo data feed as::

       data = bt.feeds.YahooFinanceData(
           ...
           version='',
           ...
       )

     of the offline Yahoo data feed as::

       data = bt.feeds.YahooFinanceCSVData(
           ...
           version='',
           ...
       )

     It might be that the online service comes back (the service was
     *discontinued* without any announcement ... it might as well come back)

or

  2. Only for Offline files downloaded before the change happened, the
     following can also be done::

       data = bt.feeds.YahooLegacyCSV(
           ...
           ...
       )

     The new ``YahooLegacyCSV`` simply automates using ``version=''``

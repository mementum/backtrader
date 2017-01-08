Extending a Datafeed
#####################

Issues in GitHub are actually pushing into finishing documentation parts or
helping me to understand if ``backtrader`` has the ease of use and flexibility I
envisioned from the first moments and the decisions made along the way.

In this case is `Issue #9 <https://github.com/mementum/backtrader/issues/9>`_.

The question finally seems to boil down to:

  - Can the end user easily extend the existing mechanisms to add extra
    information in the form of lines that gets passed along other existing price
    information spots like ``open``, ``high``, etc?

As far as I understand the question the answer is: **Yes**

The poster seems to have these requirements (from `Issue #6
<https://github.com/mementum/backtrader/issues/6>`_):

  - A data source which is being parsed into CSV format
  - Using ``GenericCSVData`` to load the information

    This generic csv support was developed in response to this `Issue #6
    <https://github.com/mementum/backtrader/issues/6>`_

  - An extra field which apparently contains P/E information which needs to be
    passed along the parsed CSV Data

Let's build on the :ref:`csv-data-feed-development` and
:ref:`generic-csv-datafeed` example posts.

Steps:

  - Assume the P/E information is being set in the CSV data which is parsed

  - Use ``GenericCSVData`` as the base class

  - Extend the existng lines (open/high/low/close/volumen/openinterest) with
    ``pe``

  - Add a parameter to let the caller determine the column position of the P/E
    information

The result::

  from backtrader.feeds import GenericCSVData

  class GenericCSV_PE(GenericCSVData):

      # Add a 'pe' line to the inherited ones from the base class
      lines = ('pe',)

      # openinterest in GenericCSVData has index 7 ... add 1
      # add the parameter to the parameters inherited from the base class
      params = (('pe', 8),)


And the job is done ...

Later and when using this data feed inside a strategy::

  import backtrader as bt

  ....

  class MyStrategy(bt.Strategy):

      ...

      def next(self):

          if self.data.close > 2000 and self.data.pe < 12:
              # TORA TORA TORA --- Get off this market
              self.sell(stake=1000000, price=0.01, exectype=Order.Limit)
      ...


Plotting that extra P/E line
============================

There is obviously no automated plot support for that extra line in the data
feed.

The best alternative would be to do a SimpleMovingAverage on that line and
plot it in a separate axis::

  import backtrader as bt
  import backtrader.indicators as btind

  ....

  class MyStrategy(bt.Strategy):

      def __init__(self):

          # The indicator autoregisters and will plot even if no obvious
	  # reference is kept to it in the class
          btind.SMA(self.data.pe, period=1, subplot=False)

      ...

      def next(self):

          if self.data.close > 2000 and self.data.pe < 12:
              # TORA TORA TORA --- Get off this market
              self.sell(stake=1000000, price=0.01, exectype=Order.Limit)
      ...

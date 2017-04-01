Plotting on the same axis
*************************

The previous post :ref:`future-vs-spot`, was plotting the original
data and the slightly (randomly) modified data on the same space, but not on
the same axis.

Recovering the 1st picture from that post.

.. thumbnail:: future-spot.png

One can see:

  - There are different scales on the left and right hand sides of the chart
  - This is most obvious when looking at the swinging red line (the randomized
    data) which oscillates ``+- 50`` points around the original data.

    On the chart the visual impression is that this randomized data is mostly
    always above the original data. Which is only a visual impression due to
    the different scales.

Although release ``1.9.32.116`` already had some initial support to fully plot
on the same axis, the legend labels would be duplicated (only the labels, not
the data) which was really confusing.

Release ``1.9.33.116`` cures that effect and allows full plotting on the same
axis. The usage pattern is like the one to decide with which other data to
plot. From the previous post.
::

   import backtrader as bt

   cerebro = bt.Cerebro()

   data0 = bt.feeds.MyFavouriteDataFeed(dataname='futurename')
   cerebro.adddata(data0)

   data1 = bt.feeds.MyFavouriteDataFeed(dataname='spotname')
   data1.compensate(data0)  # let the system know ops on data1 affect data0
   data1.plotinfo.plotmaster = data0
   data1.plotinfo.sameaxis = True
   cerebro.adddata(data1)

   ...

   cerebro.run()


``data1`` gets some ``plotinfo`` values to:

  - Plot on the same space as ``plotmaster`` which is ``data0``

  - Get the indication to use the ``sameaxis``

    The reason for this indication is that the platform cannot know in advance
    if the scales for each data will be compatible. That's why it will plot
    them on independent scales

The previous sample gets an additional option to plot on the ``sameaxis``. A
sample execution::

  $ ./future-spot.py --sameaxis

And the resulting chart

.. thumbnail:: future-spot-sameaxis.png

To notice:

  - Only one scale on the right hand side
  - And now the randomized data seems to clearly oscillate around the original
    data which is the expected visual behavior

Sample Usage
============
::

  $ ./future-spot.py --help
  usage: future-spot.py [-h] [--no-comp] [--sameaxis]

  Compensation example

  optional arguments:
    -h, --help  show this help message and exit
    --no-comp
    --sameaxis


Sample Code
===========

.. literalinclude:: future-spot.py
   :language: python
   :lines: 21-

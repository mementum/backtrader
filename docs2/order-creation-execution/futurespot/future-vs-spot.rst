Futures and Spot Compensation
*****************************

Release ``1.9.32.116`` adds support for an interesting use case presented in
the `Community <https://community.backtrader.com/>`_

  - Start a trade with a future, which includes **physical delivery**
  - Have an indicator tell you something
  - If needed be, close the position by operating on the spot price, effectively
    canceling the physical delivery, be it for receiving the goods or for
    having to deliver them (and hopefully making a profit)

    The future expires on the same day the operation on the spot price takes
    place

That means:

  - The platform is fed with data points from two different assets
  - The platform has to somehow understand the assets are related and that
    operations on the *spot* price will close positions open on the *future*

    In reality, the future is not closed, only the physical delivery is
    *compensated*

Using that *compensation* concept, ``backtrader`` adds a way to let the user
communicate to the platform that things on one data feed will have compensating
effects on another. The usage pattern
::

   import backtrader as bt

   cerebro = bt.Cerebro()

   data0 = bt.feeds.MyFavouriteDataFeed(dataname='futurename')
   cerebro.adddata(data0)

   data1 = bt.feeds.MyFavouriteDataFeed(dataname='spotname')
   data1.compensate(data0)  # let the system know ops on data1 affect data0
   cerebro.adddata(data1)

   ...

   cerebro.run()

Putting it all together
=======================

An example is always worth a thousand posts, so let's put all the pieces
together for it.

  - Use one of the standard sample feeds from the ``backtrader`` sources. This
    will be the future
  - Simulate a similar but distinct price, by reusing the same feed and adding a
    filter which will randomly move the price some points above/below, to
    create a spread. As simple as:

    .. literalinclude:: future-spot.py
       :language: python
       :lines: 29-32

  - Plotting on the same axis will mix the default included ``BuyObserver``
    markers and therefore the standard observers will be disabled and manually
    readded to plot with different per-data markers

  - Positions will be entered randomly and exited 10 days later

    This doesn't match future expiration periods, but this is just putting the
    functionality in place and not checking a trading calendar

  .. note:: A simulation including execution on the spot price on the day of
	    future expiration would require activating ``cheat-on-close`` to
	    make sure the orders are executed when the future expires. This is
	    not needed in this sample, because the expiration is being chosen
	    at random.

  - Notice that the strategy

    - ``buy`` operations are executed on ``data0``
    - ``sell`` operations are executed on ``data1``

    .. literalinclude:: future-spot.py
       :language: python
       :lines: 41-54

The execution::

  $ ./future-spot.py --no-comp

With this graphical output.

.. thumbnail:: future-spot.png

And it works:

  - ``buy`` operations are signaled with a green triangle pointing upwards and
    the legend tells us they belong to ``data0`` as expected

  - ``sell`` operations are signaled with an arrow pointing downwards and
    the legend tells us they belong to ``data1`` as expected

  - Trades are being closed, even if they are being open with ``data0`` and
    being closed with ``data1``, achieving the desired effect (which in real
    life is avoiding the physical delivery of the goods acquired by means of
    the *future*)

One could only imagine what would happen if the same logic is applied without
the *compensation* taking place. Let's do it::

  $ ./future-spot.py --no-comp

And the output

.. thumbnail:: future-spot-nocomp.png

It should be quite obvious that this fails miserably:

  - The logic expects positions on ``data0`` to be closed by the operations on
    ``data1`` and to only open positions on ``data0`` when not in the market

  - But *compensation* has been deactivated and the intial operation on
    ``data0`` (green triangle) is never closed, so no other operation can never
    be initiated and short positions on ``data1`` start accumulating.

Sample Usage
============
::

  $ ./future-spot.py --help
  usage: future-spot.py [-h] [--no-comp]

  Compensation example

  optional arguments:
    -h, --help  show this help message and exit
    --no-comp

Sample Code
===========

.. literalinclude:: future-spot.py
   :language: python
   :lines: 21-

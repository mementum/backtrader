Fillers
#######

The *backtrader* broker simulation has a default strategy when it comes to
using volume for order execution:

  - Ignore volume

This is based on 2 premises:

  - Trade in markets liquid enough to fully absorb *buy/sell* orders in one go
  - Real volume matching requires a real wolrd

    A quick example is a ``Fill or Kill`` order. Even down to the *tick*
    resolution and with enough volume for a *fill*, the *backtrader* broker
    cannot know how many extra actors happen to be in the market to
    discriminate if such an order would be or would not be matched to stick to
    the ``Fill`` part or if the order should be ``Kill``

But the *broker* can accept *Volume Fillers* which determine how much of the
volume at a given point in time has to be used for *order matching*.

The fillers signature
=====================

A *filler* in the *backtrader* ecosystem can be any *callable* which matches
the following signature::

  callable(order, price, ago)

Where:

  - ``order`` is the order which is going to be executed

    This object gives access to the ``data`` object which is the target of the
    operation, creation sizes/prices, execution prices/sizes/remaining sizes
    and other details

  - ``price`` at which the order is going to be executed

  - ``ago`` is the index to the ``data`` in the *order* in which to look for
    the volume and price elements

    In almost all cases this will be ``0`` (current point in time) but in a
    corner case to cover ``Close`` orders this may be ``-1``

    To for example access the bar volume do::

      barvolume = order.data.volume[ago]

The callable can be a function or for example an instance of a class
supporting the ``__call__`` method, like in::

  class MyFiller(object):
      def __call__(self, order, price, ago):
          pass

Adding a Filler to the broker
=============================

The most straightforward method is to use the ``set_filler``::

  import backtrader as bt

  cerebro = Cerebro()
  cerebro.broker.set_filler(bt.broker.fillers.FixedSize())

The second choice is to completely replace the ``broker``, although this is
probably only meant for subclasses of ``BrokerBack`` which have rewritten
portions of the functionality::

  import backtrader as bt

  cerebro = Cerebro()
  filler = bt.broker.fillers.FixedSize()
  newbroker = bt.broker.BrokerBack(filler=filler)
  cerebro.broker = newbroker


The sample
==========

The *backtrader* sources contain a sample named ``volumefilling`` which allows
to test some of the integrated ``fillers`` (initially all)


Reference
=========

.. currentmodule:: backtrader.fillers

.. autoclass:: FixedSize
.. autoclass:: FixedBarPerc
.. autoclass:: BarPointPerc

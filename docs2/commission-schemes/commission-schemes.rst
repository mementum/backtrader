Commissions: Stocks vs Futures
------------------------------

Agnosticity
===========

Before going forward let's remember that ``backtrader`` tries to remain agnostic
as to what the data represents. Different commission schemes can be applied to
the same data set.

Let's see how it can be done.

Using the broker shortcuts
==========================

This keeps the end user away from ``CommissionInfo`` objects because a
commission scheme can be *created/set* with a single function call. Within the
regular ``cerebro`` creation/set-up process, just add a call to
``setcommission`` over the ``broker`` member attribute. The following call sets
a usual commission scheme for **Eurostoxx50** futures when working with
*Interactive Brokers*::

   cerebro.broker.setcommission(commission=2.0, margin=2000.0, mult=10.0)

Since most users will usually just test a single instrument, that's all that's
down to it. If you have given a ``name`` to your data feed, because several
instruments are being considered simultaneously on a chart, this call can be
slightly extended to look as follows::

   cerebro.broker.setcommission(commission=2.0, margin=2000.0, mult=10.0, name='Eurostoxxx50')

In this case this on-the-fly commission scheme will only applied to instruments
whose name matches ``Eurostoxx50``.

The meaning of the setcommission parameters
===========================================

  - ``commission`` (default: ``0.0``)

    Monetary units in absolute or percentage terms each **action** costs.

    In the above example it is 2.0 euros per contract for a ``buy`` and again
    2.0 euros per contract for a ``sell``.

    The important issue here is when to use absolute or percentage values.

      - If ``margin`` evaluates to ``False`` (it is False, 0 or None for
	example) then it will be considered that ``commission`` expresses a
	percentage of the ``price`` times ``size`` operatin value

      - If ``margin`` is something else, it is considered the operations are
	happenning on a ``futures`` like intstrument and ``commission`` is a
	fixed price per ``size`` contracts

  - ``margin`` (default: ``None``)

    Margin money needed when operating with ``futures`` like instruments. As
    expressed above

      - If a **no** ``margin`` is set, the ``commission`` will be understood to
	be indicated in percentage and applied to ``price * size`` components of
	a ``buy`` or ``sell`` operation

      - If a ``margin`` is set, the ``commission`` will be understood to be a
	fixed value which is multiplied by the ``size`` component of ``buy`` or
	``sell`` operation

  - ``mult`` (default: 1.0)

    For ``future`` like instruments this determines the multiplicator to apply
    to profit and loss calculations.

    This is what makes futures attractive and risky at the same time.

  - ``name`` (default: None)

    Limit the application of the commission scheme to instruments matching
    ``name``

    This can be set during the creation of a data feed.

    If left unset, the scheme will apply to any data present in the system.


Two examples now: stocks vs futures
===================================

The futures example from above::

   cerebro.broker.setcommission(commission=2.0, margin=2000.0, mult=10.0)

A example for stocks::

   cerebro.broker.setcommission(commission=0.005)  # 0.5% of the operation value

.. note::

   The 2nd syntax doesn't set *margin* and *mult* and *backtrader* attempts a
   smart approach by considering the commission to be ``%`` based.

   To fully specify commission schemes, a subclass of ``CommissionInfo`` needs
   to be created

Creating permanent Commission schemes
=====================================

A more permanent commission scheme can be created by working directly with
``CommissionInfo`` classes. The user could choose to have this definition
somewhere::

  import backtrader as bt

  commEurostoxx50 = bt.CommissionInfo(commission=2.0, margin=2000.0, mult=10.0)

To later apply it in another Python module with ``addcommissioninfo``::

  from mycomm import commEurostoxx50

  ...

  cerebro.broker.addcommissioninfo(commEuroStoxx50, name='Eurostoxxx50')

``CommissionInfo`` is an object which uses a ``params`` declaration just like
other objects in the ``backtrader`` environment. As such the above can be also
expressed as::

  import backtrader as bt

  class CommEurostoxx50(bt.CommissionInfo):
      params = dict(commission=2.0, margin=2000.0, mult=10.0)

And later::

  from mycomm import CommEurostoxx50

  ...

  cerebro.broker.addcommissioninfoCommEuroStoxx50(), name='Eurostoxxx50')


Now a "real" comparison with a SMA Crossover
============================================

Using a SimpleMovingAverage crossover as the entry/exit signal the same data set
is going to be tested with a ``futures`` like commission scheme and then with a
``stocks`` like one.

.. note::
   Futures positions could also not only be given the enter/exit behavior but a
   reversal behavior on each occassion. But this example is about comparing the
   commission schemes.

The code (see at the bottom for the full strategy) is the same and the
scheme can be chosen before the strategy is defined.

.. literalinclude:: ./strategy-with-commission.py
   :language: python
   :lines: 29-35

Just set ``futures_like`` to false to run with the ``stocks`` like scheme.

Some logging code has been added to evaluate the impact of the differrent
commission schemes. Let's concentrate on just the 2 first operations.

For futures::

  2006-03-09, BUY CREATE, 3757.59
  2006-03-10, BUY EXECUTED, Price: 3754.13, Cost: 2000.00, Comm 2.00
  2006-04-11, SELL CREATE, 3788.81
  2006-04-12, SELL EXECUTED, Price: 3786.93, Cost: 2000.00, Comm 2.00
  2006-04-12, OPERATION PROFIT, GROSS 328.00, NET 324.00
  2006-04-20, BUY CREATE, 3860.00
  2006-04-21, BUY EXECUTED, Price: 3863.57, Cost: 2000.00, Comm 2.00
  2006-04-28, SELL CREATE, 3839.90
  2006-05-02, SELL EXECUTED, Price: 3839.24, Cost: 2000.00, Comm 2.00
  2006-05-02, OPERATION PROFIT, GROSS -243.30, NET -247.30

For stocks::

  2006-03-09, BUY CREATE, 3757.59
  2006-03-10, BUY EXECUTED, Price: 3754.13, Cost: 3754.13, Comm 18.77
  2006-04-11, SELL CREATE, 3788.81
  2006-04-12, SELL EXECUTED, Price: 3786.93, Cost: 3786.93, Comm 18.93
  2006-04-12, OPERATION PROFIT, GROSS 32.80, NET -4.91
  2006-04-20, BUY CREATE, 3860.00
  2006-04-21, BUY EXECUTED, Price: 3863.57, Cost: 3863.57, Comm 19.32
  2006-04-28, SELL CREATE, 3839.90
  2006-05-02, SELL EXECUTED, Price: 3839.24, Cost: 3839.24, Comm 19.20
  2006-05-02, OPERATION PROFIT, GROSS -24.33, NET -62.84

The 1st operation has the following prices:

  - BUY (Execution) -> 3754.13 / SELL (Execution) -> 3786.93

    - Futures Profit & Loss (with commission): 324.0
    - Stocks Profit & Loss (with commission): -4.91

  Hey!! Commission has fully eaten up any profit on the ``stocks`` operation
  but has only meant a small dent to the ``futures`` one.

The 2nd operation:

  - BUY (Execution) -> ``3863.57`` / SELL (Execution) -> ``3389.24``

    - Futures Profit & Loss (with commission): ``-247.30``
    - Stocks Profit & Loss (with commission): ``-62.84``

  The bite has been sensibly larger for this negative operation with ``futures``

But:

  - Futures accumulated net profit & loss: ``324.00 + (-247.30) = 76.70``
  - Stocks accumulated net profit & loss: ``(-4.91) + (-62.84) = -67.75``

The accumulated effect can be seen on the charts below, where it can also be
seen that at the end of the full year, futures have produced a larger profit,
but have also suffered a larger drawdown (were deeper underwater)

But the important thing: whether ``futures`` or ``stocks`` ... **it can be
backtested.**

Commissions for futures
=======================

.. thumbnail:: ./commission-futures.png

Commissions for stocks
=======================

.. thumbnail:: ./commission-stocks.png


The code
========

.. literalinclude:: ./strategy-with-commission.py
   :language: python
   :lines: 21-


Reference
=========

.. currentmodule:: backtrader

.. autoclass:: CommInfoBase

.. autoclass:: CommissionInfo

   .. automethod:: get_leverage
   .. automethod:: getsize
   .. automethod:: getoperationcost
   .. automethod:: getvaluesize
   .. automethod:: getvalue
   .. automethod:: get_margin
   .. automethod:: getcommission
   .. automethod:: _getcommission
   .. automethod:: profitandloss
   .. automethod:: cashadjust
   .. automethod:: get_credit_interest
   .. automethod:: _get_credit_interest

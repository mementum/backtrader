Cheat On Open
*************

Release ``1.9.44.116`` adds support for ``Cheat-On-Open``. This seems to be a
demanded feature for people who go *all-in*, having made a calculation after
the close of a bar, but expecting to be matched against the ``open`` price.

Such a use case fails when the *opening* price gaps (up or down, depending on
whether ``buy`` or ``sell`` is in effect) and the cash is not enough for an
*all-in* operation. This forces the broker to reject the operation.

And although people can try to look into the future with a positive ``[1]``
index approach, this requires preloading data which is not always available.

The pattern::

  cerebro = bt.Cerebro(cheat_on_open=True)

This:

  - Activates an extra cycle in the system which calls the methods in the
    strategy ``next_open``, ``nextstart_open`` and ``prenext_open``

    The decision to have an additional family of methods has been made to make
    a clear separation between the regular methods which operate on the basis
    that the prices being examined are no longer available and the future is
    unknown and the operation in cheating mode.

    This also avoids having 2 calls to the regular ``next`` method.

The following holds true when inside a ``xxx_open`` method:

  - The indicators have not been recalculated and hold the values that were
    last seen during the previous cycle in the equivalent ``xxx`` regular
    methods

  - The broker has not yet evaluated the pending orders for the new cycle and
    new orders can be introduced which will be evaluated if possible.

Notice that:

  - ``Cerebro`` also has a ``broker_coo`` (default: ``True``) parameter which
    tells cerebro that if ``cheat-on-open`` has been activated, it shall try to
    activate it also in the broker if possible.

    The simulation broker has a parameter named: ``coo`` and a method to set it
    named ``set_coo``

Trying cheat-on-open
====================

The sample below has a strategy with 2 different behaviors:

  - If *cheat-on-open* is *True*, it will only operate from ``next_open``

  - If *cheat-on-open* is *False*, it will only operate from ``next``

In both cases the matching price must be the **same**

  - If not cheating, the order is issued at the end of the previous day and
    will be matched with the next incoming price which is the ``open`` price

  - If cheating, the order is issued on the same day it is executed. Because
    the order is issued before the broker has evaluated orders, it will also be
    matched with the next incoming price, the ``open`` price.

    This second scenario, allows calculation of exact stakes for *all-in*
    strategies, because one can directly access the current ``open`` price.

In both cases

  - The current ``open`` and ``close`` prices will be printed from ``next``.

Regular execution::

  $ ./cheat-on-open.py --cerebro cheat_on_open=False

  ...
  2005-04-07 next, open 3073.4 close 3090.72
  2005-04-08 next, open 3092.07 close 3088.92
  Strat Len 68 2005-04-08 Send Buy, fromopen False, close 3088.92
  2005-04-11 Buy Executed at price 3088.47
  2005-04-11 next, open 3088.47 close 3080.6
  2005-04-12 next, open 3080.42 close 3065.18
  ...

.. thumbnail:: cheating-off.png


The order:

  - Is issued on 2005-04-08 after the *close*
  - It is executed on 2005-04-11 with the ``open`` price of ``3088.47``

Cheating execution::

  $ ./cheat-on-open.py --cerebro cheat_on_open=True

  ...
  2005-04-07 next, open 3073.4 close 3090.72
  2005-04-08 next, open 3092.07 close 3088.92
  2005-04-11 Send Buy, fromopen True, close 3080.6
  2005-04-11 Buy Executed at price 3088.47
  2005-04-11 next, open 3088.47 close 3080.6
  2005-04-12 next, open 3080.42 close 3065.18
  ...

.. thumbnail:: cheating-on.png

The order:

  - Is issued on 2005-04-11 before the *open*
  - It is executed on 2005-04-11 with the ``open`` price of ``3088.47``

And the overall result as seen on the chart is also the same.

Conclusion
==========

Cheating on the open allows issuing orders before the open which can for
example allow the exact calculation of stakes for *all-in* scenarios.

Sample usage
============
::

  $ ./cheat-on-open.py --help
  usage: cheat-on-open.py [-h] [--data0 DATA0] [--fromdate FROMDATE]
                          [--todate TODATE] [--cerebro kwargs] [--broker kwargs]
                          [--sizer kwargs] [--strat kwargs] [--plot [kwargs]]

  Cheat-On-Open Sample

  optional arguments:
    -h, --help           show this help message and exit
    --data0 DATA0        Data to read in (default:
                         ../../datas/2005-2006-day-001.txt)
    --fromdate FROMDATE  Date[time] in YYYY-MM-DD[THH:MM:SS] format (default: )
    --todate TODATE      Date[time] in YYYY-MM-DD[THH:MM:SS] format (default: )
    --cerebro kwargs     kwargs in key=value format (default: )
    --broker kwargs      kwargs in key=value format (default: )
    --sizer kwargs       kwargs in key=value format (default: )
    --strat kwargs       kwargs in key=value format (default: )
    --plot [kwargs]      kwargs in key=value format (default: )


Sample source
=============

.. literalinclude:: cheat-on-open.py
   :language: python
   :lines: 21-

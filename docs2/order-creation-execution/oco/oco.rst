OCO orders
**********

Release ``1.9.34.116`` adds ``OCO`` (aka *One Cancel Others*) to the
backtesting arsenal.

.. note:: This is only implemented in backtesting and there isn't yet an
	  implementation for live brokers

.. note:: Updated with release ``1.9.36.116``. Interactive Brokers support for
	  ``StopTrail``, ``StopTrailLimit`` and ``OCO``.

	    - ``OCO`` Specify always the 1st order in a group as parameter
	      ``oco``

	    - ``StopTrailLimit``: the broker simulation and the ``IB`` broker
	      have the asme behavior. Specify: ``price`` as the initial stop
	      trigger price (specify also ``trailamount``) and then ``plimi``
	      as the initial limit price. The difference between the two will
	      determine the ``limitoffset`` (the distance at which the limit
	      price remains from the stop trigger price)

The usage pattern tries to remain user friendly. As such and if the logic in
the strategy has decided it is the moment to issue orders, using ``OCO`` can be
done like this::

  def next(self):
      ...
      o1 = self.buy(...)
      ...
      o2 = self.buy(..., oco=o1)
      ...
      o3 = self.buy(..., oco=o1)  # or even oco=o2, o2 is already in o1 group

Easy. The 1st order ``o1`` will something like the group leader. ``o2`` and
``o3`` become part of the **OCO Group** by specifying ``o1`` with the ``oco``
named argument.  See that the comment in the snippet indicates that ``o3``
could have also become part of the group by specifying ``o2`` (which as already
part of the group)

With the group formed the following will happen:

  - If any order in the group is executed, cancelled or expires, the other
    orders will be cancelled

The sample below puts the ``OCO`` concept in play. A standard execution with a plot::

  $ ./oco.py --broker cash=50000 --plot

.. note:: cash is increased to ``50000``, because the asset reaches values of
	  ``4000`` and 3 orders of ``1`` item would require at least ``12000``
	  monetary units (the default in the broker is ``10000``)

With the following chart.

.. thumbnail:: oco.png

which actually doesn't provide much information (it is a standard ``SMA
Crossover`` strategy). The sample does the following:

  - When the fast *SMA* crosses the slow *SMA* to the upside 3 orders are
    issued

  - ``order1`` is a ``Limit`` order which will expire in ``limdays`` days
    (parameter to the strategy) with the ``close`` price reduced by a
    percentage as the limit price

  - ``order2`` is a ``Limit`` order with a much longer period to expire and a
    much more reduced limit price.

  - ``order3`` is a ``Limit`` order which further reduces the limit price

As such the execution of ``order2`` and ``order3`` is not going to happen
because:

  - ``order1`` will be executed first and this should trigger the cancellation
    of the others

or

  - ``order1`` will expire and this will trigger the the cancellation of the
    others

The system keeps the ``ref`` identifier of the 3 orders and will only issue new
``buy`` orders if the three ``ref`` identifiers are seen in ``notify_order`` as
either ``Completed``, ``Cancelled``, ``Margin`` or ``Expired``

Exiting is simply done after holding the position for some bars.

To try to keep track of the actual execution, textual output is produced. Some
of it::

  2005-01-28: Oref 1 / Buy at 2941.11055
  2005-01-28: Oref 2 / Buy at 2896.7722
  2005-01-28: Oref 3 / Buy at 2822.87495
  2005-01-31: Order ref: 1 / Type Buy / Status Submitted
  2005-01-31: Order ref: 2 / Type Buy / Status Submitted
  2005-01-31: Order ref: 3 / Type Buy / Status Submitted
  2005-01-31: Order ref: 1 / Type Buy / Status Accepted
  2005-01-31: Order ref: 2 / Type Buy / Status Accepted
  2005-01-31: Order ref: 3 / Type Buy / Status Accepted
  2005-02-01: Order ref: 1 / Type Buy / Status Expired
  2005-02-01: Order ref: 3 / Type Buy / Status Canceled
  2005-02-01: Order ref: 2 / Type Buy / Status Canceled
  ...
  2006-06-23: Oref 49 / Buy at 3532.39925
  2006-06-23: Oref 50 / Buy at 3479.147
  2006-06-23: Oref 51 / Buy at 3390.39325
  2006-06-26: Order ref: 49 / Type Buy / Status Submitted
  2006-06-26: Order ref: 50 / Type Buy / Status Submitted
  2006-06-26: Order ref: 51 / Type Buy / Status Submitted
  2006-06-26: Order ref: 49 / Type Buy / Status Accepted
  2006-06-26: Order ref: 50 / Type Buy / Status Accepted
  2006-06-26: Order ref: 51 / Type Buy / Status Accepted
  2006-06-26: Order ref: 49 / Type Buy / Status Completed
  2006-06-26: Order ref: 51 / Type Buy / Status Canceled
  2006-06-26: Order ref: 50 / Type Buy / Status Canceled
  ...
  2006-11-10: Order ref: 61 / Type Buy / Status Canceled
  2006-12-11: Oref 63 / Buy at 4032.62555
  2006-12-11: Oref 64 / Buy at 3971.8322
  2006-12-11: Oref 65 / Buy at 3870.50995
  2006-12-12: Order ref: 63 / Type Buy / Status Submitted
  2006-12-12: Order ref: 64 / Type Buy / Status Submitted
  2006-12-12: Order ref: 65 / Type Buy / Status Submitted
  2006-12-12: Order ref: 63 / Type Buy / Status Accepted
  2006-12-12: Order ref: 64 / Type Buy / Status Accepted
  2006-12-12: Order ref: 65 / Type Buy / Status Accepted
  2006-12-15: Order ref: 63 / Type Buy / Status Expired
  2006-12-15: Order ref: 65 / Type Buy / Status Canceled
  2006-12-15: Order ref: 64 / Type Buy / Status Canceled

With the following happening:

  - The 1st batch of orders is issued. Order 1 expires and 2 and 3 are
    cancelled. As expected.

  - Some months later another batch of 3 orders is issued. In this case Order
    49 gets ``Completed`` and 50 and 51 are immediately cancelled

  - The last batch is just like the 1st


Let's check now the behavior without ``OCO``::

  $ ./oco.py --strat do_oco=False --broker cash=50000

  2005-01-28: Oref 1 / Buy at 2941.11055
  2005-01-28: Oref 2 / Buy at 2896.7722
  2005-01-28: Oref 3 / Buy at 2822.87495
  2005-01-31: Order ref: 1 / Type Buy / Status Submitted
  2005-01-31: Order ref: 2 / Type Buy / Status Submitted
  2005-01-31: Order ref: 3 / Type Buy / Status Submitted
  2005-01-31: Order ref: 1 / Type Buy / Status Accepted
  2005-01-31: Order ref: 2 / Type Buy / Status Accepted
  2005-01-31: Order ref: 3 / Type Buy / Status Accepted
  2005-02-01: Order ref: 1 / Type Buy / Status Expired

And that's it, which isn't much (no order execution, not much need for a chart
either)

  - The batch of orders is issued
  - Order 1 expires, but because the strategy has gotten the parameter
    ``do_oco=False``, orders 2 and 3 are not made part of the ``OCO`` group

  - Orders 2 and 3 are therefore not cancelled and because the default
    expiration delta is ``1000`` days later, they never expire with the
    available data for the sample (2 years of data)

  - The system never issues a 2nd bath of orders.

Sample usage
============
::

  $ ./oco.py --help
  usage: oco.py [-h] [--data0 DATA0] [--fromdate FROMDATE] [--todate TODATE]
                [--cerebro kwargs] [--broker kwargs] [--sizer kwargs]
                [--strat kwargs] [--plot [kwargs]]

  Sample Skeleton

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

Sample Code
===========

.. literalinclude:: oco.py
   :language: python
   :lines: 21-


Target Orders
#############

Until version ``1.8.10.96`` smart staking was possible with *backtrader* over
the *Strategy* methods: ``buy`` and ``sell``. It was all about adding a
``Sizer`` to the equation which is responsible for the size of the stake.

What a *Sizer* cannot do is decide if the operation has to be a *buy* or a
*sell*. And that means that a new concept is needed in which a small
intelligence layer is added to make such decision.

Here is where the family of ``order_target_xxx`` methods in the *Strategy* come
into play. Inspired by the ones in ``zipline``, the methods offer the chance to
simply specify the final *target*, be the target:

  - ``size`` -> amount of shares, contracts in the portfolio of a specific
    asset
  - ``value`` -> value in monetary units of the asset in the portfolio
  - ``percent`` -> percentage (from current portfolio) value of the asset in
    the current portfolio

.. note:: The reference for the methods can be found in :doc:`../strategy`. The
	  summary is that the methods use the same *signature* as ``buy`` and
	  ``sell`` except for the parameter ``size`` which is replaced by the
	  parameter ``target``

In this case it is all about specifying the final *target* and the method
decides if an operation will be a *buy* or a *sell*. The same logic applies to
the 3 methods. Let's tart with ``order_target_size``

  - If the *target* is greater than the position a *buy* is issued, with the
    difference ``target - position_size``

    Examples:

      - Pos: ``0``, *target*: ``7`` -> *buy(size=7 - 0)* -> *buy(size=7)*

      - Pos: ``3``, *target*: ``7`` -> *buy(size=7 - 3)* -> *buy(size=4)*

      - Pos: ``-3``, *target*: ``7`` -> *buy(size=7 - -3)* -> *buy(size=10)*

      - Pos: ``-3``, *target*: ``-2`` -> *buy(size=-2 - -3)* -> *buy(size=1)*

  - If the *target* is smaller than the position a *sell* is issued with the
    difference ``position_size - target``

    Examples:

      - Pos: ``0``, *target*: ``-7`` -> *sell(size=0 - -7)* -> *sell(size=7)*

      - Pos: ``3``, *target*: ``-7`` -> *sell(size=3 - -7)* -> *sell(size=10)*

      - Pos: ``-3``, *target*: ``-7`` -> *sell(size=-3 - -7)* -> *sell(size=4)*

      - Pos: ``3``, *target*: ``2`` -> *sell(size=3 - 2)* -> *sell(size=1)*


When targetting a value with ``order_target_value``, the current *value* of the
asset in the portfolio and the *position size* are both taken into account to
decide what the final underlying operation will be. The reasoning:

  - If *position size* is negative (*short*) and the *target value* has to be
    greater than the current value, this means: *sell* more

As such the logic works as follows:

  - If ``target > value`` and ``size >=0`` -> *buy*

  - If ``target > value`` and ``size < 0`` -> *sell*

  - If ``target < value`` and ``size >= 0`` -> *sell*

  - If ``target < value`` and ``size* < 0`` -> *buy*

The logic for ``order_target_percent`` is the same as that of
``order_target_value``. This method simply takes into account the current total
value of the portfolio to determine the *target value* for the asset.


The Sample
**********

*backtrader* tries to have a sample for each new functionality and this is no
exception. No bells and whistles, just something to test the results are as
expected. This one is under the ``order_target`` directory in the samples.

The logic in the sample is rather dumb and only meaant for testing:

  - During *odd months* (Jan, Mar, ...), use the *day* as target (in the case
    of ``order_target_value`` multiplying the day by ``1000``)

    This mimics an increasing *target*

  - During *even months* (Feb, Apr, ...) use ``31 - day`` as the *target*

    This mimics an decreasing *target*

order_target_size
=================

Let's see what happens in *Jan* and *Feb*.
::

  $ ./order_target.py --target-size -- plot
  0001 - 2005-01-03 - Position Size:     00 - Value 1000000.00
  0001 - 2005-01-03 - Order Target Size: 03
  0002 - 2005-01-04 - Position Size:     03 - Value 999994.39
  0002 - 2005-01-04 - Order Target Size: 04
  0003 - 2005-01-05 - Position Size:     04 - Value 999992.48
  0003 - 2005-01-05 - Order Target Size: 05
  0004 - 2005-01-06 - Position Size:     05 - Value 999988.79
  ...
  0020 - 2005-01-31 - Position Size:     28 - Value 999968.70
  0020 - 2005-01-31 - Order Target Size: 31
  0021 - 2005-02-01 - Position Size:     31 - Value 999954.68
  0021 - 2005-02-01 - Order Target Size: 30
  0022 - 2005-02-02 - Position Size:     30 - Value 999979.65
  0022 - 2005-02-02 - Order Target Size: 29
  0023 - 2005-02-03 - Position Size:     29 - Value 999966.33
  0023 - 2005-02-03 - Order Target Size: 28
  ...


In *Jan* the *target* starts at ``3`` with the 1st trading day of the year and
increases. And the *position* size moves initially from ``0`` to ``3`` and then
in increments of ``1``.

Finishing *Jan* the last *order_target* is for ``31`` and that *position size*
is reported when entering the 1st day of *Feb*, when the new *target side* is
requested to be ``30`` and goes changing along with the position in decrements
of `´1``.

.. thumbnail:: order_target_size.png

order_target_value
==================

A similar behavior is expected from *target values*
::

  $ ./order_target.py --target-value --plot
  0001 - 2005-01-03 - Position Size:     00 - Value 1000000.00
  0001 - 2005-01-03 - data value 0.00
  0001 - 2005-01-03 - Order Target Value: 3000.00
  0002 - 2005-01-04 - Position Size:     78 - Value 999854.14
  0002 - 2005-01-04 - data value 2853.24
  0002 - 2005-01-04 - Order Target Value: 4000.00
  0003 - 2005-01-05 - Position Size:     109 - Value 999801.68
  0003 - 2005-01-05 - data value 3938.17
  0003 - 2005-01-05 - Order Target Value: 5000.00
  0004 - 2005-01-06 - Position Size:     138 - Value 999699.57
  ...
  0020 - 2005-01-31 - Position Size:     808 - Value 999206.37
  0020 - 2005-01-31 - data value 28449.68
  0020 - 2005-01-31 - Order Target Value: 31000.00
  0021 - 2005-02-01 - Position Size:     880 - Value 998807.33
  0021 - 2005-02-01 - data value 30580.00
  0021 - 2005-02-01 - Order Target Value: 30000.00
  0022 - 2005-02-02 - Position Size:     864 - Value 999510.21
  0022 - 2005-02-02 - data value 30706.56
  0022 - 2005-02-02 - Order Target Value: 29000.00
  0023 - 2005-02-03 - Position Size:     816 - Value 999130.05
  0023 - 2005-02-03 - data value 28633.44
  0023 - 2005-02-03 - Order Target Value: 28000.00
  ...

There is an extra line of information telling what the actual *data value* (in
the portfolio) is. This helps in finding out if the *target value* has been
reachec.

The initial target is ``3000.0`` and the reported initial value is
``2853.24``. The question here is whether this is *close enough*. And the
answer is *Yes*

  - The sample uses a ``Market`` order at the end of a daily bar and the last
    available price to calculate a *target size* which meets the *target value*

  - The execution uses then the ``open`` price of the next day and this is
    unlikely to be the previous ``close``

Doing it in any other way would mean one is *cheating* him/herfself.

The next *target value* and *final value* are much closer: ``4000`` and
``3938.17``.

When changing into *Feb* the *target value* starts decreasing from ``31000`` to
``30000`` and ``29000`. So does the *data value* with from ``30580.00`` to
``30706.56`` and then to ``28633.44``. Wait:

  - ``30580`` -> ``30706.56`` is a positive change

    Indeed. In this case the calculated *size* for the *target value* met an
    *opening price* which bumped the value to ``30706.56``

How this effect can be avoided:

  - The sample uses a ``Market`` type execution for the orders and this effect
    cannot be avoided

  - The methods ``order_target_xxx`` allow specifying the *execution type* and
    *price*.

    One could specify ``Limit`` as the execution order and let the price be the
    *close* price (chosen by the method if nothing else be provided) or even
    provide specific pricing

.. thumbnail:: order_target_value.png

order_target_value
==================

In this case it is simply a percentage of the current portfolio value.
::

  $ ./order_target.py --target-percent --plot
  0001 - 2005-01-03 - Position Size:     00 - Value 1000000.00
  0001 - 2005-01-03 - data percent 0.00
  0001 - 2005-01-03 - Order Target Percent: 0.03
  0002 - 2005-01-04 - Position Size:     785 - Value 998532.05
  0002 - 2005-01-04 - data percent 0.03
  0002 - 2005-01-04 - Order Target Percent: 0.04
  0003 - 2005-01-05 - Position Size:     1091 - Value 998007.44
  0003 - 2005-01-05 - data percent 0.04
  0003 - 2005-01-05 - Order Target Percent: 0.05
  0004 - 2005-01-06 - Position Size:     1381 - Value 996985.64
  ...
  0020 - 2005-01-31 - Position Size:     7985 - Value 991966.28
  0020 - 2005-01-31 - data percent 0.28
  0020 - 2005-01-31 - Order Target Percent: 0.31
  0021 - 2005-02-01 - Position Size:     8733 - Value 988008.94
  0021 - 2005-02-01 - data percent 0.31
  0021 - 2005-02-01 - Order Target Percent: 0.30
  0022 - 2005-02-02 - Position Size:     8530 - Value 995005.45
  0022 - 2005-02-02 - data percent 0.30
  0022 - 2005-02-02 - Order Target Percent: 0.29
  0023 - 2005-02-03 - Position Size:     8120 - Value 991240.75
  0023 - 2005-02-03 - data percent 0.29
  0023 - 2005-02-03 - Order Target Percent: 0.28
  ...

And the information has been changed to see the ``%`` the data represents in
the portfolio.

.. thumbnail:: order_target_percent.png

Sample Usage
************
::

  $ ./order_target.py --help
  usage: order_target.py [-h] [--data DATA] [--fromdate FROMDATE]
                         [--todate TODATE] [--cash CASH]
                         (--target-size | --target-value | --target-percent)
                         [--plot [kwargs]]

  Sample for Order Target

  optional arguments:
    -h, --help            show this help message and exit
    --data DATA           Specific data to be read in (default:
                          ../../datas/yhoo-1996-2015.txt)
    --fromdate FROMDATE   Starting date in YYYY-MM-DD format (default:
                          2005-01-01)
    --todate TODATE       Ending date in YYYY-MM-DD format (default: 2006-12-31)
    --cash CASH           Ending date in YYYY-MM-DD format (default: 1000000)
    --target-size         Use order_target_size (default: False)
    --target-value        Use order_target_value (default: False)
    --target-percent      Use order_target_percent (default: False)
    --plot [kwargs], -p [kwargs]
                          Plot the read data applying any kwargs passed For
                          example: --plot style="candle" (to plot candles)
                          (default: None)


Sample Code
***********

.. literalinclude:: order_target.py
   :language: python
   :lines: 21-

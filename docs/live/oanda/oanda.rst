
Oanda
#####

The integration with Oanda supports both:

  - *Live Data* feeding
  - *Live Trading*

Requirements
************

  - ``oandapy``

    Install it with: ``pip install git+https://github.com/oanda/oandapy.git``

  - ``pytz`` (optional and not really recommended)

    Given the worlwide and 24x7 nature of Forex, the choice is work in ``UTC``
    time. You may still work with your desired output timezone if wished.

Sample Code
***********

The sources contain a full sample under:

  - ``samples/oandatest/oandatest.py``

Oanda - the store
*****************

The store is the keystone of the live data feed/trade support, providing a
layer of adaptation between the *Oanda* API and the needs of a data feed
and a broker proxy.

  - Providesaccess to getting a *broker* instance with the method:

    - ``OandaStore.getbroker(*args, **kwargs)``

  - Provides access to getter *data* feed instances

    - ``OandaStore.getedata(*args, **kwargs)``

      In this case many of the ``**kwargs`` are common to data feeds like
      ``dataname``, ``fromdate``, ``todate``, ``sessionstart``, ``sessionend``,
      ``timeframe``, ``compression``

      The data may provide other params. Check the reference below.

Mandatory parameters
====================

In order to successfully connect to *Oanda*, the following parameters are
mandatory:

  - ``token`` (default:``None``): API access token

  - ``account`` (default: ``None``): account id

  This are provided by *Oanda*

Whether to connect to the *practice* server or to the real server, use:

  - ``practice`` (default: ``False``): use the test environment

The account has to be periodically checked to get the *cash* and *value*. The
periodicity can be controlled with:

  - ``account_tmout`` (default: ``10.0``): refresh period for account
    value/cash refresh


Oanda feeds
***********

Instantiating the data:

  - Pass the symbol according to the Oanda guidelines

    - *EUR/USDD* following the guidelines from Oanda has to be specified as  as
      ``EUR_USD``. Instantiate it as::

	data = oandastore.getdata(dataname='EUR_USD', ...)

Time management
===============

Unless a ``tz`` parameter (a *pytz-compatible* object) is passed to the data
feed, all time output is in ``UTC`` format as expressed above.


Backfilling
------------

*backtrader* makes no special request to *Oanda*. For small timeframes the
backfilling returned by *Oanda* on the *practice* servers has been ``500`` bars
long


OandaBroker - Trading Live
**************************

Using the broker
================

To use the *OandaBroker*, the standard broker simulation instance created by
*cerebro* has to be replaced.

Using the *Store* model (preferred)::

  import backtrader as bt

  cerebro = bt.Cerebro()
  oandastore = bt.stores.OandaStore()
  cerebro.broker = oandastore.getbroker()  # or cerebro.setbroker(...)

Broker - Initial Positions
==========================

The broker supports a single parameter:

  - ``use_positions`` (default:``True``): When connecting to the broker
    provider use the existing positions to kickstart the broker.

    Set to ``False`` during instantiation to disregard any existing
    position

Opperations
-----------

There is no change with regards to the standar usage. Just use the methods
available in the strategy (see the ``Strategy`` reference for a full
explanation)

  - ``buy``
  - ``sell``
  - ``close``
  - ``cancel``

Order Execution Types
=====================

*Oanda* supports almost all of the order execution types needed by
*backtrader* with the exception of *Close*.

As such the order execution types are limited to:

  - ``Order.Market``
  - ``Order.Limit``
  - ``Order.Stop``
  - ``Order.StopLimit`` (using *Stop* and *upperBound* / *lowerBound* prices)

Order Validity
==============

The same validity notion available during backtesting (with ``valid`` to
``buy`` and ``sell``) is available and with the same meaning. As such, the
``valid`` parameter is translated as follows for *Oanda Orders* for the
following values:

  - ``None`` translates to *Good Til Cancelled*

    Because no validity has been specified it is understood that the order must
    be valid until cancelled

  - ``datetime/date`` translates to *Good Til Date*

  - ``timedelta(x)`` translates to *Good Til Date* (here ``timedelta(x) !=
    timedelta()``)

    This is interpreted as a signal to have an order be valid from ``now`` +
    ``timedelta(x)``

  - ``timedelta() or 0`` translates to *Session*

    A value has been passed (instead of ``None``) but is *Null* and is
    interpreted as an order valid for the current *day* (session)

Notifications
=============

The standard ``Order`` status will be notified to a *strategy* over the method
``notify_order`` (if overridden)

  - ``Submitted`` - the order has been sent to TWS
  - ``Accepted`` - the order has been placed
  - ``Rejected`` - Use for real rejections and when no other status is known
    during order creation
  - ``Partial`` - a partial execution has taken place
  - ``Completed`` - the order has been fully executed
  - ``Canceled`` (or ``Cancelled``)
  - ``Expired`` - when an order is cancelled due to expiry

Reference
*********

OandaStore
==========

.. currentmodule:: backtrader.stores
.. autoclass:: OandaStore


OandaBroker
===========

.. currentmodule:: backtrader.brokers
.. autoclass:: OandaBroker

OandaData
=========

.. currentmodule:: backtrader.feeds
.. autoclass:: OandaData

Orders
######

``Cerebro`` is the key control system in ``backtrader`` and ``Strategy`` (a
subclass) is the key control point of the end user. The latter needs a chaining
method to other parts of the system and that's where **orders** play a key
role.

*Orders* translate the decisions made by the logic in a ``Strategy`` into a
message suitable for the ``Broker`` to execute an action. This is done with:

  - *Creation*

    Through Strategy's methods: ``buy```, ``sell`` and ``close``
    (:doc:`strategy`) which return an ``order`` instance as a reference

  - *Cancellation*

    Through Strategy's method: ``cancel`` (:doc:`strategy`) which takes an
    order instance to operate on

And the *orders* serve also as a communication method back to the user, to
notify how things are running in the broker.

  - *Notification*

    To Strategy method: ``notify_order`` (:doc:`strategy`) which reports an
    ``order`` instance


Order creation
==============

When invoking the ``buy``, ``sell`` and ``close`` the following parameters
apply for creation:

    - ``data`` (default: ``None``)

      For which data the order has to be created. If ``None`` then the
      first data in the system, ``self.datas[0] or self.data0`` (aka
      ``self.data``) will be used

    - ``size`` (default: ``None``)

      Size to use (positive) of units of data to use for the order.

      If ``None`` the ``sizer`` instance retrieved via ``getsizer`` will
      be used to determine the size.

    - ``price`` (default: ``None``)

      Price to use (live brokers may place restrictions on the actual
      format if it does not comply to minimum tick size requirements)

      ``None`` is valid for ``Market`` and ``Close`` orders (the market
      determines the price)

      For ``Limit``, ``Stop`` and ``StopLimit`` orders this value
      determines the trigger point (in the case of ``Limit`` the trigger
      is obviously at which price the order should be matched)

    - ``plimit`` (default: ``None``)

      Only applicable to ``StopLimit`` orders. This is the price at which
      to set the implicit *Limit* order, once the *Stop* has been
      triggered (for which ``price`` has been used)

    - ``exectype`` (default: ``None``)

      Possible values:

      - ``Order.Market`` or ``None``. A market order will be executed
        with the next available price. In backtesting it will be the
        opening price of the next bar

      - ``Order.Limit``. An order which can only be executed at the given
        ``price`` or better

      - ``Order.Stop``. An order which is triggered at ``price`` and
        executed like an ``Order.Market`` order

      - ``Order.StopLimit``. An order which is triggered at ``price`` and
        executed as an implicit *Limit* order with price given by
        ``pricelimit``

    - ``valid`` (default: ``None``)

      Possible values:

        - ``None``: this generates an order that will not expire (aka
          *Good till cancel*) and remain in the market until matched or
          canceled. In reality brokers tend to impose a temporal limit,
          but this is usually so far away in time to consider it as not
          expiring

        - ``datetime.datetime`` or ``datetime.date`` instance: the date
          will be used to generate an order valid until the given
          datetime (aka *good till date*)

        - ``Order.DAY`` or ``0`` or ``timedelta()``: a day valid until
          the *End of the Session* (aka *day* order) will be generated

        - ``numeric value``: This is assumed to be a value corresponding
          to a datetime in ``matplotlib`` coding (the one used by
          ``backtrader``) and will used to generate an order valid until
          that time (*good till date*)

    - ``tradeid`` (default: ``0``)

      This is an internal value applied by ``backtrader`` to keep track
      of overlapping trades on the same asset. This ``tradeid`` is sent
      back to the *strategy* when notifying changes to the status of the
      orders.

    - ``**kwargs``: additional broker implementations may support extra
      parameters. ``backtrader`` will pass the *kwargs* down to the
      created order objects

      Example: if the 4 order execution types directly supported by
      ``backtrader`` are not enough, in the case of for example
      *Interactive Brokers* the following could be passed as *kwargs*::

        orderType='LIT', lmtPrice=10.0, auxPrice=9.8

      This would override the settings created by ``backtrader`` and
      generate a ``LIMIT IF TOUCHED`` order with a *touched* price of 9.8
      and a *limit* price of 10.0.

.. note:: The ``close`` method will examine the current position and
	  correspondingly use ``buy`` or ``sell`` to effectively **close** the
	  position. ``size`` will also be automatically calculated unless the
	  parameter is an input from the user, in which case a partial *close*
	  or a *reversal* can be achieved


Order notification
==================

To receive notifications the ``notify_order`` method has to be overriden in the
user subclassed ``Strategy`` (the default behavior is to do nothing). The
following applies to those notifications:

  - Issued before the strategy's ``next`` method is called

  - May (and will) happen several times for the same *order* with the same or
    different status during the same *next* cycle.

    An *order* may be submitted to the *broker* and be *accepted* and its
    execution *completed* before ``next`` will be invoked again.

    In this case at least 3 notifications will happen with the following
    ``status`` values:

      - ``Order.Submitted`` because the order was sent to the *broker*

      - ``Order.Accepted`` because the order was taken by the *broker* and
	awaits potential execution

      - ``Order.Completed`` because in the example it was quickly matched and
	completely filled (which may be the case usually for ``Market`` orders)

Notifications may happen even several times for the same status in the case of
``Order.Partial``. This status will not be seen in the *backtesting* broker
(which doesn't consider volume when matching) but it will for sure be set by
real brokers.

Real brokers may issue one or more executions before updating a position, and
this group of executions will make up for an ``Order.Partial`` notification.

Actual execution data is in the attribute: ``order.executed`` which is an
object of type ``OrderData`` (see below for the reference), with usual fields
as ``size`` and ``price``

The values at the time of creation are stored in ``order.created`` which
remains unchanged throughout the lifecycle of an ``order``

Order Status values
===================

The following are defined:

  - ``Order.Created``: set when the ``Order`` instance is created. Never to be
    seen by end-users unless ``order`` instances are manually created rather
    than through ``buy``, ``sell`` and ``close``

  - ``Order.Submitted``: set when the ``order`` instance has been transmitted
    to the ``broker``. This simply means it has been *sent*. In *backtesting*
    mode this will be an immediate action, but it may take actual *time* with a
    real broker, which may receive the order and only first notify when it has
    been forwarded to an exchange

  - ``Order.Accepted``: the ``broker`` has taken the order and it is in the
    system (or already in a exchange) awaiting execution according to the set
    parameters like execution type, size, price and validity

  - ``Order.Partial``: the ``order`` has been partially
    executed. ``order.executed`` contains the current filled ``size`` and
    average price.

    ``order.executed.exbits`` contains a complete list of ``ExecutionBits``
    detailing the partial fillings

  - ``Order.Complete``: the ``order`` has been completely filled
    average price.

  - ``Order.Rejected``: the ``broker`` has rejected the order. A parameter
    (like for example ``valid`` to determine its lifetime) may not be accepted
    by the ``broker`` and the ``order`` cannot be accepted.

    The reason will be notified via the ``notify_store`` method of the
    ``strategy``. Although this may seem awkward, the reason is that real life
    brokers will notify this over an event, which may or may not be direclty
    related to the order. But the notification from the broker can still be
    seen in ``notify_store``.

    This status will not be seen in the *backtesting* broker

  - ``Order.Margin``: the order execution would imply a margin call and the
    previously accepted order has been taken off the system

  - ``Order.Cancelled`` (or ``Order.Canceled``): confirmation of the user
    requested cancellation

    It must be taken into account that a request to *cancel* an order via the
    ``cancel`` method of the strategy is no guarantee of cancellation. The
    order may have been already executed but such execution may not have yet
    notified by the broker and/or the notification may not have yet been
    delivered to the strategy

  - ``Order.Expired``: a previously accepted *order** which had a time validity
    has expired and ben taken off the system


Reference: Order and associated classes
=======================================

These objects are the generic classes in the ``backtrader`` ecosystem. They may
been extended and/or contain extra embedded information when operating with
other brokers. See the reference of the appropriate broker


.. currentmodule:: backtrader.order

.. autoclass:: Order

.. autoclass:: OrderData

.. autoclass:: OrderExecutionBit

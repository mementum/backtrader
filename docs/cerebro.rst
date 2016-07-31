Cerebro
#######

This class is the cornerstone of ``backtrader`` because it serves as a central
point for:

  1. Gathering all inputs (*Data Feeds*), actors (*Stratgegies*), spectators
     (*Observers*), critics (*Analyzers*) and documenters (*Writers*) ensuring the
     show still goes on at any moment.

  2. Execute the backtesting/or live data feeding/trading

  3. Returning the results

  4. Giving access to the plotting facilities


Gathering input
***************

  0. Start by creating a ``cerebro``::

       cerebro = bt.Cerebro(**kwargs)

     Some ``**kwargs`` to control execution are supported, see the reference
     (the same arguments can be applied later to the ``run`` method)

  1. Add ``Datas``

     The most usual pattern is ``cerebro.adddata(data)``, where ``data`` is a
     *data feed* already instantiated. Example::

       data = bt.BacktraderCSVData(dataname='mypath.days', timeframe=bt.TimeFrame.Days)
       cerebro.adddata(data)

     *Resampling* and *Replaying* a data is possible and follows the same pattern::

       data = bt.BacktraderCSVData(dataname='mypath.min', timeframe=bt.TimeFrame.Minutes)
       cerebro.resampledata(data, timeframe=bt.TimeFrame.Days)

     or::

       data = bt.BacktraderCSVData(dataname='mypath.min', timeframe=bt.TimeFrame.Minutes)
       cerebro.replaydatadata(data, timeframe=bt.TimeFrame.Days)

     The system can accept any number of datas, including mixing regular data
     with resampled and/or replayed data. Of course some of this combinationns
     will for sure make no sense and a restriction apply in order to be able to
     combine datas: *time aligment*. See the
     :doc:`data-multitimeframe/data-multitimeframe`,
     :doc:`data-resampling/data-resampling` - Resampling` and
     :doc:`data-replay/data-replay` sections.

  2. Add ``Strategies``

     Unlike the ``datas`` which are already an instance of a class, ``cerebro``
     takes directly the ``Strategy`` class and the arguments to pass to it. The
     rationale behind:  *in an optimization scenario the class will be
     instantiated several times and passed different arguments*

     Even if no *optimization* is run, the pattern still applies::

       cerebro.addstrategy(MyStrategy, myparam1=value1, myparam2=value2)

     When *optimizing* the parameters have to be added as iterables. See the
     *Optimization* section for a detailed explanation. The basic pattern::

       cerebro.optstrategy(MyStrategy, myparam1=range(10, 20))

     Which will run ``MyStrategy`` 10 times with ``myparam1`` taking values
     from 10 to 19 (remember ranges in Python are half-open and ``20`` will not
     be reached)

  3. Other elements

     There are some other elements which can be added to enhance the
     backtesting experience. See the appropriate sections for it. The methods
     are:

       - ``addwriter``

       - ``addanalyzer``

       - ``addobserver``

  4. Changing the broker

     Cerebro will use the default broker in ``backtrader``, but this can be
     overriden::

       broker = MyBroker()
       cerebro.broker = broker  # property using getbroker/setbroker methods

  5. Receive notifications

     If *datas* and/or *brokers* send notifications (or a *store* provider
     which creates them) they will be received through the
     ``Cerebro.notify_store`` method. There are three (3) ways to work with
     these notifications

     - Add a *callback* to a ``cerebro`` instance via the
       ``addnotifycallback(callback)`` call. The callback has to support this
       signature::

	 callback(msg, *args, **kwargs)

       The actual ``msg``, ``*args`` and ``**kwargs`` received are
       implementation defined (depend entirely on the *data/broker/store*) but
       in general one should expect them to be *printable* to allow for
       reception and experimentation.

     - Override the ``notify_store`` method in the ``Strategy`` subclass which
       is added to a ``cerebro`` instance.

       The signature: ``notify_store(self, msg, *args, **kwargs)``

     - Subclass ``Cerebro`` and override ``notify_store`` (same signature as in
       the ``Strategy``)

       This should be the least preferred method


Execute the backtesting
***********************

There is a single method to do it, but it supports several options (which can
be also specified when instantiating) to decide how to run::

  result = cerebro.run(**kwargs)

The arguments for the different supported ways of execuing the backtesting:

  - ``preload`` (default: ``True``)

    Whether to preload the different ``datas`` passed to cerebro for the
    Strategies

  - ``runonce`` (default: ``True``)

    Calculate ``Indicators`` in a single pass in a tight inner *for loop* to
    speed up the entire system.  Strategies and Observers will always be run on
    an event based (next) basis to ensure the logic is executed for each and
    every step

  - ``maxcpus`` (default: ``None`` -> all available cores)

    How many cores to use simultaneously for optimization

  - ``stdstats`` (default: ``True``)

    If ``True`` default Observers will be added: Broker (Cash and Value),
    Trades and BuySell

  - ``live`` (default: False)

    If no data has reported itself as *live* (via the data's ``islive``
    method but the end user still want to run in ``live`` mode, this
    parameter can be set to true

    This will simulatenously deactivate ``preload`` and ``runonce``. It
    will have no effect on memory saving schemes.

    Run ``Indicators`` in vectorized mode to speed up the entire system.
    Strategies and Observers will always be run on an event based basis

  - ``exactbars`` (default: False)

    With the default value each and every value stored in a line is kept in
    memory

    Possible values:
      - ``True`` or ``1``: all "lines" objects reduce memory usage to the
        automatically calculated minimum period.

        If a Simple Moving Average has a period of 30, the underlying data
        will have always a running buffer of 30 bars to allow the
        calculation of the Simple Moving Average

        - This setting will deactivate ``preload`` and ``runonce``
        - Using this setting also deactivates **plotting**

      - ``-1``: datas and indicators/operations at strategy level will keep
        all data in memory.

        For example: a ``RSI`` internally uses the indicator ``UpDay`` to
        make calculations. This subindicator will not keep all data in
        memory

        - This allows to keep ``plotting`` and ``preloading`` active.

        - ``runonce`` will be deactivated

      - ``-2``: datas and indicators kept as attributes of the strategy
        will keep all data in memory.

        For example: a ``RSI`` internally uses the indicator ``UpDay`` to
        make calculations. This subindicator will not keep all data in
        memory

        If in the ``__init__`` something like
        ``a = self.data.close - self.data.high`` is defined, then ``a``
        will not keep all data in memory

        - This allows to keep ``plotting`` and ``preloading`` active.

        - ``runonce`` will be deactivated

  - ``writer`` (default: ``False``)

    If set to True a default WriterFile will be created which will print to
    stdout. It will be added to the strategy (in addition to any other
    writers added by the user code)

  - ``tradehistory`` (default: ``False``)

    If set to True, it will activate update event logging in each trade for
    all strategies. This can also be accomplished on a per strategy basis
    with the strategy method ``set_tradehistory``

Standard Observers
==================

``cerebro`` (unless otherwise specified) automatically instantiates *three*
standard `observers`

  - A *Broker* observer which keeps track of ``cash`` and ``value`` (portfolio)
  - A *Trades* observer which should show how effective each trade has been
  - A *Buy/Sell* observer which should document when operations are executed

Should a cleaner plotting be wished just disable them with ``stdstats=False``


Returning the results
*********************

``cerebro`` returns the instances of the strategies it created during
backtesting. This allows to analyze what they did, because all elements in the
strategies are accessible::

  result = cerebro.run(**kwargs)

The format of ``result`` returned by ``run`` will vary depending on whether *optimization*
is used (a *strategy* was added with ``optstrategy``):

  - All strategies added with ``addstrategy``

    ``result`` will be a ``list`` of the instances run during the backtesting

  - 1 or more strategies were added with ``optstrategy``

    ``result`` will be a ``list`` of ``list``. Each internal list will contain
    the strategies after each optimization run


Giving access to the plotting facilities
****************************************

As an extra an if ``matplotlib`` is installed, the strategies can be
plotted. With the usual pattern being::

  cerebro.plot()

See below for the reference and the section :doc:`plotting/plotting`


Backtesting logic
*****************

Brief outline of the flow of things:

  0. Deliver any store notifications

  1. Ask datas to deliver the next set of ticks/bars

     The 1st data inserted into the system is the ``datamaster`` and the system
     will wait for it to deliver a tick

     The other datas are, more or less, slaves to the ``datamaster`` and:

       - If the next tick to deliver is newer (datetime-wise) than the one
	 delivered by the ``datamaster`` it will not be delivered

       - May return without delivering a new tick for a number of reasons

       The logic was designed to easily synchronize multiple datas and datas
       with different timeframes

  2. Notify the strategy about queued broker notifications of orders, trades
     and cash/value

  3. Tell the broker to accept queued orders and execute the pending orders
     with the new data

  4. Call the strategies' ``next`` method to let the strategy evaluate the new
     data (and maybe issue orders which are queued in the broker)

     Depending on the stage it may be ``prenext`` or ``nextstart`` before the
     minimum period requirements of the strategy/indicators are met

     Internally the strategies will also kick the ``observers``,
     ``indicators``, ``analyzers``  and other active elements

  5. Tell any ``writers`` to write the data to its target

Important to take into account:

.. note::  In step ``1`` above when the *datas* deliver the new set of bars,
	   those bars are **closed**. This means the data has already happened.

	   As such, *orders* issued by the strategy in step ``4`` cannot be
	   *executed* with the data from step ``1``.

	   This means that orders will be executed with the concept of ``x +
	   1``. Where ``x`` is the bar moment at which the order was executed
	   and ``x + 1`` the next one, which is the earliest moment in time for
	   a possible order execution


Reference
=========

.. currentmodule:: backtrader

.. autoclass:: Cerebro

   .. automethod:: addstorecb

   .. automethod:: notify_store

   .. automethod:: adddatacb

   .. automethod:: notify_data

   .. automethod:: adddata

   .. automethod:: resampledata

   .. automethod:: replaydata

   .. automethod:: addstrategy

   .. automethod:: optstrategy

   .. automethod:: addindicator

   .. automethod:: addobserver

   .. automethod:: addanalyzer

   .. automethod:: addwriter

   .. automethod:: run

   .. automethod:: runstop

   .. automethod:: setbroker

   .. automethod:: getbroker

   .. automethod:: plot

   .. automethod:: addsizer

   .. automethod:: addsizer_byidx

   .. automethod:: add_signal

   .. automethod:: signal_concurrent

   .. automethod:: signal_accumulate

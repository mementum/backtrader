
Timers
******

Release ``1.9.44.116`` added *timers* to the arsenal of tools available in
*backtrader*. This functionality allows to get a call back to the
``notify_timer`` (available in ``Cerebro`` and ``Strategy``) at given points in
time, with a fine grained end-user control.

.. note:: Some corrections have been made in ``1.9.46.116``

Options
=======

  - Timer based in absolute time input or with regards to session start/end
    times

  - Timezone specification for the time specification, be it directly or via
    *pytz* compatible objects or via data feed
    session end times

  - Starting offset with regards to the specified time

  - Repetitions intervals

  - Weekdays filter (with carry over option)

  - Monthdays filter (with carry over option)

  - Custom callback filter

Usage pattern
=============

Both in ``Cerebro`` and ``Strategy`` subclasses the timer callback will be
received in the following method.
::

    def notify_timer(self, timer, when, *args, **kwargs):
        '''Receives a timer notification where ``timer`` is the timer which was
        returned by ``add_timer``, and ``when`` is the calling time. ``args``
        and ``kwargs`` are any additional arguments passed to ``add_timer``

        The actual ``when`` time can be later, but the system may have not be
        able to call the timer before. This value is the timer value and not the
        system time.
        '''

Adding timers - Via Strategy
----------------------------

Done with the method
::

    def add_timer(self, when,
                  offset=datetime.timedelta(), repeat=datetime.timedelta(),
                  weekdays=[], weekcarry=False,
                  monthdays=[], monthcarry=True,
                  allow=None,
                  tzdata=None, cheat=False,
                  *args, **kwargs):
        '''

It returns the created ``Timer`` instance.

See below for an explanation of the parameters.

Adding timers - Via Cerebro
----------------------------

Done with the same method and just the addition of the parameter ``strats``. If
set to ``True`` the timer will not only be notified to the *cerebro*, it will
also be notified to all strategies running in the system.
::

    def add_timer(self, when,
                  offset=datetime.timedelta(), repeat=datetime.timedelta(),
                  weekdays=[], weekcarry=False,
                  monthdays=[], monthcarry=True,
                  allow=None,
                  tzdata=None, cheat=False, strats=False,
                  *args, **kwargs):
        '''

It returns the created ``Timer`` instance.


When are timers called
======================

If ``cheat=False``
------------------

This is the default. In this case a timer will be called:

  - After the data feeds have loaded the new values for the current bar

  - After the broker has evaluated orders and recalculated the portfolio value

  - Before indicators have been recalculated (because this is triggered by the
    strategies)

  - Before any ``next`` method of any strategy is called

If ``cheat=True``
-----------------

In this case a timer will be called:

  - After the data feeds have loaded the new values for the current bar

  - **Before** the broker has evaluated orders and recalculated the portfolio
    value

  - And consequently before indicators have been recalculated and ``next``
    method of any strategy is called

Which allows for example the following scenario with daily bars:

  - Before the new bar is evaluated by the broker the timer is called

  - The indicators have the value from the previous day at the close and can be
    used to generate an entry/exit signal (or a flag may have been set during
    the last evaluation of ``next``)

  - Because the new prices are available, the stake can be calculated using the
    opening price. This assumes that one is for example getting a good
    indication about the ``open`` from watching the opening auction.

Running with daily bars
=======================

The sample ``scheduled.py`` defaults to running with the standard daily bars
available in the *backtrader* distribution. The parameters to the strategy

.. literalinclude:: scheduled.py
   :language: python
   :lines: 30-38

And the data has the following session times:

  - start: 09:00
  - end: 17:30

Running with just a time
::

  $ ./scheduled.py --strat when='datetime.time(15,30)'

  strategy notify_timer with tid 0, when 2005-01-03 15:30:00 cheat False
  1, 2005-01-03 17:30:00, Week 1, Day 1, O 2952.29, H 2989.61, L 2946.8, C 2970.02
  strategy notify_timer with tid 0, when 2005-01-04 15:30:00 cheat False
  2, 2005-01-04 17:30:00, Week 1, Day 2, O 2969.78, H 2979.88, L 2961.14, C 2971.12
  strategy notify_timer with tid 0, when 2005-01-05 15:30:00 cheat False
  3, 2005-01-05 17:30:00, Week 1, Day 3, O 2969.0, H 2969.0, L 2942.69, C 2947.19
  strategy notify_timer with tid 0, when 2005-01-06 15:30:00 cheat False
  ...

As specified the timer is ticking at ``15:30``. No surprises there. Let's add
an offset of 30 minutes.
::

  $ ./scheduled.py --strat when='datetime.time(15,30)',offset='datetime.timedelta(minutes=30)'

  strategy notify_timer with tid 0, when 2005-01-03 16:00:00 cheat False
  1, 2005-01-03 17:30:00, Week 1, Day 1, O 2952.29, H 2989.61, L 2946.8, C 2970.02
  strategy notify_timer with tid 0, when 2005-01-04 16:00:00 cheat False
  2, 2005-01-04 17:30:00, Week 1, Day 2, O 2969.78, H 2979.88, L 2961.14, C 2971.12
  strategy notify_timer with tid 0, when 2005-01-05 16:00:00 cheat False
  ...

And the time has changed from ``15:30`` to ``16:00`` for the timer. No
surprises. Let's do the same but referencing the start of the session.
::

  $ ./scheduled.py --strat when='bt.timer.SESSION_START',offset='datetime.timedelta(minutes=30)'

  strategy notify_timer with tid 0, when 2005-01-03 09:30:00 cheat False
  1, 2005-01-03 17:30:00, Week 1, Day 1, O 2952.29, H 2989.61, L 2946.8, C 2970.02
  strategy notify_timer with tid 0, when 2005-01-04 09:30:00 cheat False
  2, 2005-01-04 17:30:00, Week 1, Day 2, O 2969.78, H 2979.88, L 2961.14, C 2971.12
  ...

Et voilá! The time at which the callback is called is ``09:30``. And the
session start, see above, is ``09:00``. This gives the ability to simply say
that one wants to execute an action *30 minutes* after the start of the
session.

Let's add a repetition::

  $ ./scheduled.py --strat when='bt.timer.SESSION_START',offset='datetime.timedelta(minutes=30)',repeat='datetime.timedelta(minutes=30)'

  strategy notify_timer with tid 0, when 2005-01-03 09:30:00 cheat False
  1, 2005-01-03 17:30:00, Week 1, Day 1, O 2952.29, H 2989.61, L 2946.8, C 2970.02
  strategy notify_timer with tid 0, when 2005-01-04 09:30:00 cheat False
  2, 2005-01-04 17:30:00, Week 1, Day 2, O 2969.78, H 2979.88, L 2961.14, C 2971.12
  strategy notify_timer with tid 0, when 2005-01-05 09:30:00 cheat False
  ...

**There is no repetition**. The reason being that the resolution of the prices
is daily. The timer is called for the 1st time at ``09:30`` like in the
previous example. But when the system get the next batch of prices, they are
happening on the next day. And the timer can only, obviously, be called once. A
lower resolution is needed.

But before moving on to a lower resolution, let's cheat by having the timer
called before the end of the session.
::

  $ ./scheduled.py --strat when='bt.timer.SESSION_START',cheat=True

  strategy notify_timer with tid 1, when 2005-01-03 09:00:00 cheat True
  -- 2005-01-03 Create buy order
  strategy notify_timer with tid 0, when 2005-01-03 09:00:00 cheat False
  1, 2005-01-03 17:30:00, Week 1, Day 1, O 2952.29, H 2989.61, L 2946.8, C 2970.02
  strategy notify_timer with tid 1, when 2005-01-04 09:00:00 cheat True
  strategy notify_timer with tid 0, when 2005-01-04 09:00:00 cheat False
  -- 2005-01-04 Buy Exec @ 2969.78
  2, 2005-01-04 17:30:00, Week 1, Day 2, O 2969.78, H 2979.88, L 2961.14, C 2971.12
  strategy notify_timer with tid 1, when 2005-01-05 09:00:00 cheat True
  strategy notify_timer with tid 0, when 2005-01-05 09:00:00 cheat False
  ...

The strategy adds a 2nd timer with ``cheat=True``. This is added 2nd and will
therefore received the 2nd ``tid`` (*timer id*) which is ``1`` (see in the
above examples that the assigned ``tid`` was ``0``)

And ``1`` is called before ``0``, because that timer is *cheating* and is being
called before many events in the system happen (see above for the explanation)

Due to the *daily* resolution of the prices it doesn't make much of a
difference except that:

  - The strategy also issues an order right before the open ... and it is being
    matched with the opening price the next day

    This, even if cheating by acting before the open, is still the normal
    behavior, because *cheating-on-open* has also not been activated in the
    broker.

The same but with ``coo=True`` for the broker
::

  $ ./scheduled.py --strat when='bt.timer.SESSION_START',cheat=True --broker coo=True

  strategy notify_timer with tid 1, when 2005-01-03 09:00:00 cheat True
  -- 2005-01-03 Create buy order
  strategy notify_timer with tid 0, when 2005-01-03 09:00:00 cheat False
  -- 2005-01-03 Buy Exec @ 2952.29
  1, 2005-01-03 17:30:00, Week 1, Day 1, O 2952.29, H 2989.61, L 2946.8, C 2970.02
  strategy notify_timer with tid 1, when 2005-01-04 09:00:00 cheat True
  strategy notify_timer with tid 0, when 2005-01-04 09:00:00 cheat False
  2, 2005-01-04 17:30:00, Week 1, Day 2, O 2969.78, H 2979.88, L 2961.14, C 2971.12
  strategy notify_timer with tid 1, when 2005-01-05 09:00:00 cheat True
  strategy notify_timer with tid 0, when 2005-01-05 09:00:00 cheat False
  ...

And something has changed.

  - The order is issued on ``2005-01-03`` in the cheating timer

  - The order is executed on ``2005-01-03`` with the opening price

    Effectively like if one had acted on the opening auction price seconds
    before the real opening of the market.


Running with 5-minute bars
==========================

The sample ``scheduled-min.py`` defaults to running with the standard 5-minute
bars available in the *backtrader* distribution. The parameters to the strategy
are extended to include ``monthdays`` and the *carry* options

.. literalinclude:: scheduled-min.py
   :language: python
   :lines: 30-41

The data has the same session times:

  - start: 09:00
  - end: 17:30

Let's do some experiments. First a single timer.
::

  $ ./scheduled-min.py --strat when='datetime.time(15, 30)'

  1, 2006-01-02 09:05:00, Week 1, Day 1, O 3578.73, H 3587.88, L 3578.73, C 3582.99
  2, 2006-01-02 09:10:00, Week 1, Day 1, O 3583.01, H 3588.4, L 3583.01, C 3588.03
  ...
  77, 2006-01-02 15:25:00, Week 1, Day 1, O 3599.07, H 3599.68, L 3598.47, C 3599.68
  strategy notify_timer with tid 0, when 2006-01-02 15:30:00 cheat False
  78, 2006-01-02 15:30:00, Week 1, Day 1, O 3599.64, H 3599.73, L 3599.0, C 3599.67
  ...
  179, 2006-01-03 15:25:00, Week 1, Day 2, O 3634.72, H 3635.0, L 3634.06, C 3634.87
  strategy notify_timer with tid 0, when 2006-01-03 15:30:00 cheat False
  180, 2006-01-03 15:30:00, Week 1, Day 2, O 3634.81, H 3634.89, L 3634.04, C 3634.23
  ...

The timer kicks in as requested at ``15:30``. The log shows how it does that
during the 1st two days.

Adding a ``repeat`` of ``15 minutes`` to the mix
::

  $ ./scheduled-min.py --strat when='datetime.time(15, 30)',repeat='datetime.timedelta(minutes=15)'

  ...
  74, 2006-01-02 15:10:00, Week 1, Day 1, O 3596.12, H 3596.63, L 3595.92, C 3596.63
  75, 2006-01-02 15:15:00, Week 1, Day 1, O 3596.36, H 3596.65, L 3596.19, C 3596.65
  76, 2006-01-02 15:20:00, Week 1, Day 1, O 3596.53, H 3599.13, L 3596.12, C 3598.9
  77, 2006-01-02 15:25:00, Week 1, Day 1, O 3599.07, H 3599.68, L 3598.47, C 3599.68
  strategy notify_timer with tid 0, when 2006-01-02 15:30:00 cheat False
  78, 2006-01-02 15:30:00, Week 1, Day 1, O 3599.64, H 3599.73, L 3599.0, C 3599.67
  79, 2006-01-02 15:35:00, Week 1, Day 1, O 3599.61, H 3600.29, L 3599.52, C 3599.92
  80, 2006-01-02 15:40:00, Week 1, Day 1, O 3599.96, H 3602.06, L 3599.76, C 3602.05
  strategy notify_timer with tid 0, when 2006-01-02 15:45:00 cheat False
  81, 2006-01-02 15:45:00, Week 1, Day 1, O 3601.97, H 3602.07, L 3601.45, C 3601.83
  82, 2006-01-02 15:50:00, Week 1, Day 1, O 3601.74, H 3602.8, L 3601.63, C 3602.8
  83, 2006-01-02 15:55:00, Week 1, Day 1, O 3602.53, H 3602.74, L 3602.33, C 3602.61
  strategy notify_timer with tid 0, when 2006-01-02 16:00:00 cheat False
  84, 2006-01-02 16:00:00, Week 1, Day 1, O 3602.58, H 3602.75, L 3601.81, C 3602.14
  85, 2006-01-02 16:05:00, Week 1, Day 1, O 3602.16, H 3602.16, L 3600.86, C 3600.96
  86, 2006-01-02 16:10:00, Week 1, Day 1, O 3601.2, H 3601.49, L 3600.94, C 3601.27
  ...
  strategy notify_timer with tid 0, when 2006-01-02 17:15:00 cheat False
  99, 2006-01-02 17:15:00, Week 1, Day 1, O 3603.96, H 3603.96, L 3602.89, C 3603.79
  100, 2006-01-02 17:20:00, Week 1, Day 1, O 3603.94, H 3605.95, L 3603.87, C 3603.91
  101, 2006-01-02 17:25:00, Week 1, Day 1, O 3604.0, H 3604.76, L 3603.85, C 3604.64
  strategy notify_timer with tid 0, when 2006-01-02 17:30:00 cheat False
  102, 2006-01-02 17:30:00, Week 1, Day 1, O 3604.06, H 3604.41, L 3603.95, C 3604.33
  103, 2006-01-03 09:05:00, Week 1, Day 2, O 3604.08, H 3609.6, L 3604.08, C 3609.6
  104, 2006-01-03 09:10:00, Week 1, Day 2, O 3610.34, H 3617.31, L 3610.34, C 3617.31
  105, 2006-01-03 09:15:00, Week 1, Day 2, O 3617.61, H 3617.87, L 3616.03, C 3617.51
  106, 2006-01-03 09:20:00, Week 1, Day 2, O 3617.24, H 3618.86, L 3616.09, C 3618.42
  ...
  179, 2006-01-03 15:25:00, Week 1, Day 2, O 3634.72, H 3635.0, L 3634.06, C 3634.87
  strategy notify_timer with tid 0, when 2006-01-03 15:30:00 cheat False
  180, 2006-01-03 15:30:00, Week 1, Day 2, O 3634.81, H 3634.89, L 3634.04, C 3634.23
  ...

As expected the 1st call is triggered at ``15:30`` and then starts repeating
every 15 minutes until the end of the session at ``17:30``. When the new session
kicks in, the timer has been reset to ``15:30`` again.

And now with cheating before the session start
::

  $ ./scheduled-min.py --strat when='bt.timer.SESSION_START',cheat=True

  strategy notify_timer with tid 1, when 2006-01-02 09:00:00 cheat True
  -- 2006-01-02 09:05:00 Create buy order
  strategy notify_timer with tid 0, when 2006-01-02 09:00:00 cheat False
  1, 2006-01-02 09:05:00, Week 1, Day 1, O 3578.73, H 3587.88, L 3578.73, C 3582.99
  -- 2006-01-02 09:10:00 Buy Exec @ 3583.01
  2, 2006-01-02 09:10:00, Week 1, Day 1, O 3583.01, H 3588.4, L 3583.01, C 3588.03
  ...

Order creation is t ``09:05:00`` and execution at ``09:10:00`` because the
broker is not in *cheat-on-open* mode. Let's set it ...
::

  $ ./scheduled-min.py --strat when='bt.timer.SESSION_START',cheat=True --broker coo=True

  strategy notify_timer with tid 1, when 2006-01-02 09:00:00 cheat True
  -- 2006-01-02 09:05:00 Create buy order
  strategy notify_timer with tid 0, when 2006-01-02 09:00:00 cheat False
  -- 2006-01-02 09:05:00 Buy Exec @ 3578.73
  1, 2006-01-02 09:05:00, Week 1, Day 1, O 3578.73, H 3587.88, L 3578.73, C 3582.99
  2, 2006-01-02 09:10:00, Week 1, Day 1, O 3583.01, H 3588.4, L 3583.01, C 3588.03
  ...

And the issuing time and execution time are ``09:05:00`` with the execution
price being the opening price at ``09:05:00``.

Additional scenarios
====================

Timers allow specifying on which days they have to be executed by passing a
list of days (integers following the iso spec, where Mon=1 and Sun=7) as in

  - ``weekdays=[5]`` which would ask for the timer to only be valid on Fridays

    In case a Friday is a non-trading day and the timer should kick-in on the
    next trading day, one can add ``weekcarry=True``

Similar to it, one can decide to act on the 15th day of each month with:

  - ``monthdays=[15]``

    In case the 15th happens to be non-trading day and the timer should kick-in
    on the next trading day, one can add ``monthcarry=True``

There isn't an implementation for things like:  *the 3rd Friday of March, June,
September and December* (futures/options expirations), but there is a
possibility to implement rules by passing:

  - ``allow=callable`` where the callable accepts  ``datetime.date``
    instance. Notice this is not a ``datetime.datetime`` instance, because the
    *allow* callable is only meant to decide if a given day is suitable for
    timers or not.

    To implement something like the rule laid out above::

      class FutOpExp(object):
          def __init__(self):
	      self.fridays = 0
	      self.curmonth = -1

          def __call__(self, d):
	      _, _, isowkday = d.isocalendar()

	      if d.month != self.curmonth:
	          self.curmonth = d.month
                  self.fridays = 0

              # Mon=1 ... Sun=7
              if isowkday == 5 and self.curmonth in [3, 6, 9, 12]:
                  self.fridays += 1

                  if self.friday == 3:  # 3rd Friday
                      return True  # timer allowed

              return False  # timer disallowed

    And one would pass ``allow=FutOpeExp()`` to the creation of the timer

    This would allow a timer to kick in on the 3rd Friday of those months and
    may be close positions before the futures expire.


Parameters to ``add_timer``
===========================

  - ``when``: can be

    - ``datetime.time`` instance (see below ``tzdata``)
    - ``bt.timer.SESSION_START`` to reference a session start
    - ``bt.timer.SESSION_END`` to reference a session end

 - ``offset`` which must be a ``datetime.timedelta`` instance

   Used to offset the value ``when``. It has a meaningful use in
   combination with ``SESSION_START`` and ``SESSION_END``, to indicated
   things like a timer being called ``15 minutes`` after the session
   start.

  - ``repeat`` which must be a ``datetime.timedelta`` instance

    Indicates if after a 1st call, further calls will be scheduled
    within the same session at the scheduled ``repeat`` delta

    Once the timer goes over the end of the session it is reset to the
    original value for ``when``

  - ``weekdays``: a **sorted** iterable with integers indicating on
    which days (iso codes, Monday is 1, Sunday is 7) the timers can
    be actually invoked

    If not specified, the timer will be active on all days

  - ``weekcarry`` (default: ``False``). If ``True`` and the weekday was
    not seen (ex: trading holiday), the timer will be executed on the
    next day (even if in a new week)

  - ``monthdays``: a **sorted** iterable with integers indicating on
    which days of the month a timer has to be executed. For example
    always on day *15* of the month

    If not specified, the timer will be active on all days

  - ``monthcarry`` (default: ``True``). If the day was not seen
    (weekend, trading holiday), the timer will be executed on the next
    available day.

  - ``allow`` (default: ``None``). A callback which receives a
    `datetime.date`` instance and returns ``True`` if the date is
    allowed for timers or else returns ``False``

  - ``tzdata`` which can be either ``None`` (default), a ``pytz``
    instance or a ``data feed`` instance.

    ``None``: ``when`` is interpreted at face value (which translates
    to handling it as if it where UTC even if it's not)

    ``pytz`` instance: ``when`` will be interpreted as being specified
    in the local time specified by the timezone instance.

    ``data feed`` instance: ``when`` will be interpreted as being
    specified in the local time specified by the ``tz`` parameter of
    the data feed instance.

    **Note**: If ``when`` is either ``SESSION_START`` or
      ``SESSION_END`` and ``tzdata`` is ``None``, the 1st *data feed*
      in the system (aka ``self.data0``) will be used as the reference
      to find out the session times.

  - ``strats`` (default: ``False``) call also the ``notify_timer`` of
    strategies

  - ``cheat`` (default ``False``) if ``True`` the timer will be called
    before the broker has a chance to evaluate the orders. This opens
    the chance to issue orders based on opening price for example right
    before the session starts
  - ``*args``: any extra args will be passed to ``notify_timer``

  - ``**kwargs``: any extra kwargs will be passed to ``notify_timer``

Sample usage ``scheduled.py``
=============================
::

  $ ./scheduled.py --help
  usage: scheduled.py [-h] [--data0 DATA0] [--fromdate FROMDATE]
                      [--todate TODATE] [--cerebro kwargs] [--broker kwargs]
                      [--sizer kwargs] [--strat kwargs] [--plot [kwargs]]

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


Sample usage ``scheduled-min.py``
=================================
::

  $ ./scheduled-min.py --help
  usage: scheduled-min.py [-h] [--data0 DATA0] [--fromdate FROMDATE]
                          [--todate TODATE] [--cerebro kwargs] [--broker kwargs]
                          [--sizer kwargs] [--strat kwargs] [--plot [kwargs]]

  Timer Test Intraday

  optional arguments:
    -h, --help           show this help message and exit
    --data0 DATA0        Data to read in (default: ../../datas/2006-min-005.txt)
    --fromdate FROMDATE  Date[time] in YYYY-MM-DD[THH:MM:SS] format (default: )
    --todate TODATE      Date[time] in YYYY-MM-DD[THH:MM:SS] format (default: )
    --cerebro kwargs     kwargs in key=value format (default: )
    --broker kwargs      kwargs in key=value format (default: )
    --sizer kwargs       kwargs in key=value format (default: )
    --strat kwargs       kwargs in key=value format (default: )
    --plot [kwargs]      kwargs in key=value format (default: )

Sample source ``scheduled.py``
==============================

.. literalinclude:: scheduled.py
   :language: python
   :lines: 21-

Sample source ``scheduled-min.py``
==================================

.. literalinclude:: scheduled-min.py
   :language: python
   :lines: 21-

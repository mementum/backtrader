DateTime Management
###################

Up until release *1.5.0*, *backtrader* used a direct approach to time
management in that whatever datetime was calculated by *data sources* was
simply used at face value.

And the same for any user input like in the case of the *parameter*
``fromdate`` (or ``sessionstart``) which can be given to any *data source*

The approach was fine given the direct control over frozen data sources for
backtesting. It was easy to assume that the input datetimes had already been
taken care of before they entered the system.

But with 1.5.0, **live** *data sources* are supported and this forces to take
into account **datetime management**.  Such management would not be needed if
the following were always *true*:

  - A trader in New York trades the ES-Mini. The time zone for both in
    ``US/Eastern`` (or one of the aliases)

  - A trader in Berlin trades the DAX future. In this case for both the ``CET``
    (or ``Europe/Berling``) timezone applies

The direct input-output datetime approach from above would work, becase the
trader, in Berlin for example, could always do something like this::

  class Strategy(bt.Strategy):

      def next(self):

          # The DAX future opens at 08:00 CET
          if self.data.datetime.time() < datetime.time(8, 30):
	      # don't operate until the market has been running 30 minutes
	      return  #

The problem with the direct approach surfaces when the same trader in Berlin
decides to trade the ``ES-Mini``. Because the change to from *DST* happens at
different point in time in the year and this causes the time difference to be
out of sync a couple of weeks during the year. The following wouldn't always
work::

  class Strategy(bt.Strategy):

      def next(self):

          # The SPX opens at 09:30 US/Eastern all year long
          # This is most of the year 15:30 CET
	  # But it is sometimes 16:30 CET or 14:30 CET if a DST switch on-off
	  # has happened in the USA and not in Europe

	  # That's why the code below is unreliable

          if self.data.datetime.time() < datetime.time(16, 0):
	      # don't operate until the market has been running 30 minutes
	      return  #


Operation with timezones
************************

To solve the aforementioned situations and still remain compatible with the
direct input-output time approach, ``backtrader`` offers the end user the
following

Datetime Input
==============

  - As a default the platform will not touch the *datetime* provided by a data source

    - The end-user can override this input by:

      - Providing a ``tzinput`` parameter to the data source. This must be an
	object compatible with the ``datetime.tzinfo`` interface. Most likely
	the user will provide a ``pytz.timezone`` instance

    With this decision the time used internally by ``backtrader`` is considered
    to be in ``UTC-like`` format, ie:

      - If the data source has already stored it in ``UTC`` format

      - After a conversion through ``tzinput``

      - It's not really ``UTC`` but it's the reference for the user, hence
	``UTC-like``

Datetime output
===============

  - If the data feed can automatically determine the timezone for the output,
    this will be the default

    This makes sense in the case of live-feeds and especially in use cases like
    the one in which a trader in Berlin (``CET`` timezone), trades products
    with ``US/Eastern`` timezone.

    Because the trader gets always the right time and in the example above the
    *opening* time remains constant at ``09:30 US/Eastern``, rather than
    ``15:30 CET`` most of the year, but sometimes ``16:30 CET`` and sometimes
    ``14:30 CET``.

  - If it cannot be determined, then the output will be whatever was determined
    during input (the ``UTC-like``) time

  - The end user can override and determine the actual timezone for the output

      - Providing a ``tz`` parameter to the data source. This must be an object
	compatible with the ``datetime.tzinfo`` interface. Most likely the user
	will provide a ``pytz.timezone`` instance

.. note::

   Input fromt the user like for example the parameters ``fromdate`` or
   ``sessionstart`` are expected to be in sync with the actual ``tz``, be it
   automatically calculated by the *data source*, supplied by the user or left
   as default (``None``, which means direct input-output of *datetime*)

With all that in mind let's recall the Berlin trader, trading in
``US/Eastern``::

  import pytz

  import bt

  data = bt.feeds.MyFeed('ES-Mini', tz=pytz.timezone('US/Eastern'))

  class Strategy(bt.Strategy):

      def next(self):

          # This will work all year round.
	  # The data source will return in the frame of the 'US/Eastern' time
	  # zone and the user is quoting '10:00' as reference time
	  # Because in the 'US/Eastern' timezone the SPX index always starts
	  # trading at 09:30, this will always work

          if self.data.datetime.time() < datetime.time(10, 0):
	      # don't operate until the market has been running 30 minutes
	      return  #

In the case of a *data source* which can automatically determine the output
timezone::

  import bt

  data = bt.feeds.MyFeedAutoTZ('ES-Mini')

  class Strategy(bt.Strategy):

      def next(self):

          # This will work all year round.
	  # The data source will return in the frame of the 'US/Eastern' time
	  # zone and the user is quoting '10:00' as reference time
	  # Because in the 'US/Eastern' timezone the SPX index always starts
	  # trading at 09:30, this will always work

          if self.data.datetime.time() < datetime.time(10, 0):
	      # don't operate until the market has been running 30 minutes
	      return  #

Even less work than above.

Obviously ``MyFeed`` and ``MyFeedAuto`` in the example above are just dummy
names.

.. note::
   At the time of writing the only data source included in the distribution
   which can automatically determine the timezone is the one connecting to
   *Interactive Brokers*

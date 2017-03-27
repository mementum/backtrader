Filters
#######

This functionality is a relatively late addition to *backtrader* and had to be
fitted to the already existing internals. This makes it to be not as flexible
and 100% feature full as wished, but it can still serve the purpose in many
cases.

Although the implementation tried to allow plug and play filter chaining, the
pre-existing internals made it difficult to ensure that could always be
achieved. As such, some filters may be chained and some others may not.

Purpose
*******

  - Transform the values provided by a *data feed* to deliver a different *data
    feed*

The implementation was started to simplify the implementation of the two
obvious filters which can be directly used via the *cerebro* API. These are:

  - *Resampling*  (``cerebro.resampledata``)

    Here the filter transforms the ``timeframe`` and ``compression`` of the
    incoming *data feed*. For example::

      (Seconds, 1) -> (Days, 1)

    That means that the original data feed is delivery bars with a resolution
    of *1 Second*. The *Resampling* filter intercepts the data and buffers it
    until it can deliver a *1 Day* bar. This will happen when a *1 Second* bar
    from the next day is seen.

  - *Replaying* (``cerebro.replaydata``)

    For the same timeframes as above, the filter would use the *1 Second*
    resolution bars to rebuild the *1 Day* bar.

    That means that the *1 Day* bar is delivered as many times as *1 Second*
    bars are seen, updated to contain the latest information.

    This simulates, for example, how an actual trading day has developed.

    .. note:: the length of the data, ``len(data)`` and therefore the length of
	      the strategy remain unchanged as long as the *day* doesn't
	      change.

Filters at work
***************

Given an existing data feed/source you use the ``addfilter`` method of the data
feed::

  data = MyDataFeed(dataname=myname)
  data.addfilter(filter, *args, **kwargs)
  cerebro.addata(data)

And even if it happens to be compatible to the *resample/replay* filter the
following can also be done::

  data = MyDataFeed(dataname=myname)
  data.addfilter(filter, *args, **kwargs)
  cerebro.replaydata(data)


Filter Interface
****************

A ``filter`` must conform to a given interface, being this:

  - A callable which accepts this signature::

      callable(data, *args, **kwargs)

  or

  - A class which can be *instantiated* and *called*

    - During instantiation the ``__init__`` method must support the signature::

        def __init__(self, data, *args, **kwargs)

    - The ``__call__`` method bears this signature::

        def __call__(self, data, *args, **kwargs)

      The instance will be called for each new incoming values from the *data
      feed*. The ``*args`` and ``*kwargs`` are the same passed to ``__init__``

      **RETURN VALUES**:

        - ``True``: the inner data fetching loop of the data feed must retry
	  fetching data from the feed, becaue the length of the stream was
	  manipulated

	- ``False`` even if data may have been edited (example: changed
	  ``close`` price), the length of the stream has remain untouched

    In the case of a class based filter 2 additional methods can be implemented

    - ``last`` with the following signature::

	def last(self, data, *args, **kwargs)

      This will be called when the *data feed* is over, allowing the filter to
      deliver data it may have for example buffered. A typical case is
      *resampling*, because a bar is buffered until data from the next time
      period is seen. When the data feed is over, there is no new data to push
      the buffered data out.

      ``last`` offers the chance to push the buffered data out.

.. note:: It is obvious that if the *filter* supports no arguments at all and
	  will be added without any, the signatures can be simplified as in::

	    def __init__(self, data, *args, **kwargs) -> def __init__(self, data)


A Sample Filter
***************

A very quick filter implementation::

  class SessionFilter(object):
      def __init__(self, data):
          pass

      def __call__(self, data):
          if data.p.sessionstart <= data.datetime.time() <= data.p.sessionend:
              # bar is in the session
              return False  # tell outer data loop the bar can be processed

          # bar outside of the regular session times
          data.backwards()  # remove bar from data stack
          return True  # tell outer data loop to fetch a new bar

This filter:

  - Uses ``data.p.sessionstart`` and ``data.p.sessionend`` (standard data feed
    parameters) to decide if a bar is in the session.

  - If *in-the-session* the return value is ``False`` to indicate nothing was
    done and the processing of the current bar can continue

  - If *not-in-the-session*, the bar is removed from the stream and ``True`` is
    returned to indicate a new bar must be fetched.

    .. note:: the ``data.backwards()`` makes uses of the ``LineBuffer``
	      interface. This digs deep into the internals of *backtrader*.

The use of this filter:

  - Some data feeds contain *out of regular trading hours* data, which may not
    be of interest to the trader. With this filter only *in-session* bars will
    be considered.


Data Pseudo-API for Filters
***************************

In the example above it has been shown how the filter invokes
``data.backwards()`` to remove the current bar from the stream. Useful calls
from the data feed objects which are meant as a *pseudo-API for Filters* are:

  - ``data.backwards(size=1, force=False)``: removes *size* bars from the data
    stream (default is ``1``) by moving the logical pointer backwards. If
    ``force=True``, then the physical storage is also removed.

    Removing the physical storage is a delicate operation and is only meant as
    a hack for internal operations.

  - ``data.forward(value=float('NaN'), size=1)``: moves *size* bars the storage
    forward, increasing the physical storage if needed be and fills with
    ``value``

  - ``data._addtostack(bar, stash=False)``: adds ``bar`` to a stack for later
    processing. ``bar`` is an iterable containing as many values as ``lines``
    has the data feed.

    If ``stash=False`` the bar added to the stack will be consumed immediately
    by the system at the beginning of the next iteration.

    If ``stash=True`` the bar will undergo the entire loop processing including
    potentially being reparsed by filters

  - ``data._save2stack(erase=False, force=False)``: saves the current data bar
    to the stack for later processing. If ``erase=True`` then
    ``data.backwards`` will be invoked and will receive the parameter ``force``

  - ``data._updatebar(bar, forward=False, ago=0)``: uses the values in the
    iterable ``bar`` to overwrite the values in the data stream ``ago``
    positions. With the default ``ago=0`` the current bar will updated. With
    ``-1``, the previous one.


Another example: Pinkfish Filter
********************************

This is an example of a filter that can be chained, and is meant so, to another
filter, namely the *replay filter*. The *Pinkfish* name is from the library
which describes the idea in its main page: using daily data to execute
operations which would only be possible with intraday data.

To achieve the effect:

  - A daily bar will be broken in 2 componentes: ``OHL`` and then ``C``.

  - Those 2 pieces are chained with *replay* to have the following happening in
    the stream::

      With Len X     -> OHL
      With Len X     -> OHLC
      With Len X + 1 -> OHL
      With Len X + 1 -> OHLC
      With Len X + 2 -> OHL
      With Len X + 2 -> OHLC
      ...

Logic:

  - When an ``OHLC`` bar is received it is copied into an interable and broken
    down to become:

    - An ``OHL`` bar. Because this concept doesn't actually exist the *closing*
      price is replaced with the *opening* price to really form an ``OHLO``
      bar.

    - An ``C`` bar whic also doesn't exist. The reality is that it will be
      delivered like a tick ``CCCC``

    - The volume if distributed between the 2 parts

    - The current bar is removed from the stream

    - The ``OHLO`` part is put onto the stack for immediate processing

    - The ``CCCC`` part is put into the stash for processing in the next round

    - Because the stack has something for immediate processing the filter can
      return ``False`` to indicate it.

This filter works together with:

  - The *replay* filter which puts together the ``OHLO`` and ``CCCC`` parts to
    finally deliver an ``OHLC`` bar.

The use case:

  - Seeing something like if the maximum today is the highest maximum in the
    last 20 sessions an issuing a ``Close`` order which gets executed with the
    2nd tick.

The code::

  class DaySplitter_Close(bt.with_metaclass(bt.MetaParams, object)):
      '''
      Splits a daily bar in two parts simulating 2 ticks which will be used to
      replay the data:

        - First tick: ``OHLX``

          The ``Close`` will be replaced by the *average* of ``Open``, ``High``
          and ``Low``

          The session opening time is used for this tick

        and

        - Second tick: ``CCCC``

          The ``Close`` price will be used for the four components of the price

          The session closing time is used for this tick

      The volume will be split amongst the 2 ticks using the parameters:

        - ``closevol`` (default: ``0.5``) The value indicate which percentage, in
          absolute terms from 0.0 to 1.0, has to be assigned to the *closing*
          tick. The rest will be assigned to the ``OHLX`` tick.

      **This filter is meant to be used together with** ``cerebro.replaydata``

      '''
      params = (
          ('closevol', 0.5),  # 0 -> 1 amount of volume to keep for close
      )

      # replaying = True

      def __init__(self, data):
          self.lastdt = None

      def __call__(self, data):
          # Make a copy of the new bar and remove it from stream
          datadt = data.datetime.date()  # keep the date

          if self.lastdt == datadt:
              return False  # skip bars that come again in the filter

          self.lastdt = datadt  # keep ref to last seen bar

          # Make a copy of current data for ohlbar
          ohlbar = [data.lines[i][0] for i in range(data.size())]
          closebar = ohlbar[:]  # Make a copy for the close

          # replace close price with o-h-l average
          ohlprice = ohlbar[data.Open] + ohlbar[data.High] + ohlbar[data.Low]
          ohlbar[data.Close] = ohlprice / 3.0

          vol = ohlbar[data.Volume]  # adjust volume
          ohlbar[data.Volume] = vohl = int(vol * (1.0 - self.p.closevol))

          oi = ohlbar[data.OpenInterest]  # adjust open interst
          ohlbar[data.OpenInterest] = 0

          # Adjust times
          dt = datetime.datetime.combine(datadt, data.p.sessionstart)
          ohlbar[data.DateTime] = data.date2num(dt)

          # Ajust closebar to generate a single tick -> close price
          closebar[data.Open] = cprice = closebar[data.Close]
          closebar[data.High] = cprice
          closebar[data.Low] = cprice
          closebar[data.Volume] = vol - vohl
          ohlbar[data.OpenInterest] = oi

          # Adjust times
          dt = datetime.datetime.combine(datadt, data.p.sessionend)
          closebar[data.DateTime] = data.date2num(dt)

          # Update stream
          data.backwards(force=True)  # remove the copied bar from stream
          data._add2stack(ohlbar)  # add ohlbar to stack
          # Add 2nd part to stash to delay processing to next round
          data._add2stack(closebar, stash=True)

          return False  # initial tick can be further processed from stack

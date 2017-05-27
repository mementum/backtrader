
======================
 Plotting Date Ranges
======================

The release, ``1.9.31.x`` added the capability to make partial plots.

  - Either with indices to the full length array of *timestamps* kept in
    *strategy* instances

  - Or with actual ``datetime.date`` or ``datetime.datetime`` instances that
    limit what has to be plotted.

Everything still over the standard ``cerebro.plot``. Example::

  cerebro.plot(start=datetime.date(2005, 7, 1), end=datetime.date(2006, 1, 31))

Being that the straightforward way to do it for humans. Humans with extended
capabilities can actually try indices to the ``datetime`` timestamps as in::

  cerebro.plot(start=75, end=185)

A very standard sample containing a *Simple Moving Average* (on-data
plotting), a *Stochastic* (independent plotting) and a *CrossOver* of the
*Stochastic* lines is presented below. The arguments to ``cerebro.plot`` are
passed as command line arguments.

An execution with the ``date`` approach::

  ./partial-plot.py --plot 'start=datetime.date(2005, 7, 1),end=datetime.date(2006, 1, 31)'

The ``eval`` magic in python allows to directly write ``datetime.date`` in the
command line and map actually that to something sensible. The output chart

.. thumbnail:: partial-dates.png

Let's compare it with the full plot to see that data was actually skipped from
both ends::

  ./partial-plot.py --plot

The ``eval`` magic in python allows to directly write ``datetime.date`` in the
command line and map actually that to something sensible. The output chart

.. thumbnail:: full-dates.png


Sample Usage
============
::

  $ ./partial-plot.py --help
  usage: partial-plot.py [-h] [--data0 DATA0] [--fromdate FROMDATE]
                         [--todate TODATE] [--cerebro kwargs] [--broker kwargs]
                         [--sizer kwargs] [--strat kwargs] [--plot [kwargs]]

  Sample for partial plotting

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

.. literalinclude:: partial-plot.py
   :language: python
   :lines: 21-

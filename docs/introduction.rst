Introduction
============

Backtrader is Python based backtesting platform for developing home cooked indicators and trading strategies.

The platform can operate as a tick-based platform. In this mode for each bar all
objects will be called to recalculate (many times the "ticks" will be complete
bars) It can also operate in batch mode processing each all bars at once.

The tick-based approach would allow to connect to a real-time data feed. The
batch mode is much faster but operates on a existing set of bars, which is
appropriate for backtesting.

User defined objects (ex: indicators) can only provide the tick-based methods
and they will still operate in batch mode (by looping n times over the
tick-based method)

The platform has been designed to avoid external dependencies as much as
possible. As such the only things that are currently needed are:

  * Python 2.7 (development was finished when running 2.7.9, but most of it was
    done with Python 2.7.5)

Optionally:

  * matplotlib if you want to plot charts of your strategies and associated
    datas (1.4.2 has been tested)

    matplotlib will obviously pull in its own dependencies

The basic building blocks in the platform that you'll become acquainted with
are:

  * Data Feeds
  * Indicators
  * Strategies
  * Brokers
  * Commissions
  * Position Sizers
  * Analyzers
  * Plotters
  * Cerebro (the main looping engine)

Don't panic!!! One of the targets of this platform is to make most of the inner
working of the objects, relationships and interactions transparent to the
platform user. For example: a broker with a preset commission scheme (no
commission) is included along a fixed size Position sizer, a basic Analyzer and
*sensible* defaults for plotting.

Some operations are obviously the responsibility of the user, because the
platform cannot know or decide if the user wishes to base the logic of a
strategy on Moving Average or an Average True Range indicator (or maybe both
will be used or one will use the other)

The basics:

  * Create a Strategy

    - Decide on potential adjustable parameters
    - Create the Indicators you need in the Strategy
    - Lay out the logic for entering/exiting the market

  * Load a Data Feed

    - Yahoo Online and CSV is supported
    - Another CSV example format is provided

  * Create a Cerebro Engine

    - Inject the Strategy (with your parameters of choice)
    - Inject the Data Feed
    - And ... run()

Let's hope you, the user, find the platform useful and fun to work with.

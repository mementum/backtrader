Introduction
============

Backtrader is a pseudo-event driven backtesting platform for trading strategies. "Pseudo"-Event drive means your objects will be called but the actual timing for this called is not controlled by traditional events, but rather by a set of recursive loops.

This design would in theory allow to connecto to a live trading and/or data feed platform without compromising speed. At the moment this is just a possibility which is not foreseen.

The platform has been designed to avoid external dependencies as much as possible. As such the only things that are currently needed are:

  * Python 2.7 (development was finished when running 2.7.9, but most of it was done with Python 2.7.5)
  * matplotlib if you want to plot charts of your strategies and associated datas (1.4.2 has been tested)

    matplotlib will obviously pull in its own dependencies

The basic building blocks in the platform that you'll become acquainted with are:

  * Data Feeds
  * Indicators
  * Strategies
  * Broker
  * Commissions
  * Position Sizers
  * Analyzers
  * Cerebro (the main looping engine)

Don't panic!!! One of the targets of this platform is to make most of the inner working of the objects, relationships and interactions transparent to the platform user. For example: a broker with a preset commission scheme (no commission) is included along a fixed size Position sizer and a basic Analyzer.

Some operations are obviously the responsibility of the user, because the platform cannot know or decide if the user wishes to base the logic of a strategy on Moving Average or an Average True Range indicator (or maybe both will be used or one will use the other)

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

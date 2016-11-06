Introduction
############

Backtrader is Python based backtesting/trading platform for developing home cooked
indicators and trading strategies.

Features:

  - Live Data Feed and Trading with

    - Interactive Brokers (needs ``IbPy`` and benefits greatly from an
      installed ``pytz``)
    - *Visual Chart* (needs a fork of ``comtypes`` until a pull request is
      integrated in the release and benefits from ``pytz``)
    - *Oanda* (needs ``oandapy``)

  - Data feeds from csv/files, online sources or from *pandas* and *blaze*
  - Filters for datas (like breaking a daily bar into chunks to simulate intraday)
  - Multiple data feeds and multiple strategies supported
  - Multiple timeframes at once
  - Integrated Resampling and Replaying
  - Step by Step backtesting or at once (except in the evaluation of the Strategy)
  - Integrated battery of indicators
  - *TA-Lib* indicator support
  - Easy development of custom indicators
  - Analyzers (for example: TimeReturn, Sharpe Ratio, SQN) and ``pyfolio``
    integration
  - Flexible definition of commission schemes
  - Integrated broker simulation with *Market*, *Close*, *Limit*, *Stop* and
    *StopLimit* orders, slippage and continuous cash adjustmet for future-like
    instruments
  - Plotting (requires *matplotlib*)

The platform has 2 main objectives:

  1. Ease of use
  2. Go back to 1

Loosely based on the *Karate (Kid)* rules by *Mr. Miyagi*.

The basics of running this platform:

  - Create a Strategy

    - Decide on potential adjustable parameters
    - Instantiate the Indicators you need in the Strategy
    - Write down the logic for entering/exiting the market

Or alternatively:

  - Prepare some indicators to work as *long*/*short* signals

And then

  - Create a *Cerebro* Engine

    - First:

        - Inject the *Strategy*

	or

	- Inject the *Signals*

    And then:

    - Load and Inject a Data Feed
    - And do ``cerebro.run()``
    - For visual feedback execute: ``cerebro.plot()``

The platform is highly configurable

Let's hope you, the user, find the platform useful and fun to work with.

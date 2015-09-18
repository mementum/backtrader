Introduction
############

Backtrader is Python based backtesting platform for developing home cooked
indicators and trading strategies.

Features:

  - Bar by Bar (next) operation or batch mode (once) operation
  - Indicators and the addition of any custom end-user developed one
  - Strategies
  - Data Feeds from Online Sources, CSV Files, binary sources, Panda DataFrames,
    Blaze iterators
  - Data Feeds with different timeframes
  - Data Feed Resampling
  - Data Feed Replaying
  - A Broker implementation supporting
    - Margin checks
    - Commision schemes for stock-like and futures-like instruments
    - Orders: Close, Market, Limit, Stop, StopLimit
  - Position Sizers for the automatic determination of the stake
  - Optimization of Strategies (multicore capable)
  - Plotting

The development focused on two rules:

  1. Ease of use
  2. Go back to rule 1

Loosely based on the Karate (Kid) rules by Mr. Miyagi.

Some focus has been put into *speed* but without direct usage of `numpy` (for
example) the limits without creating spaghetti code have been reached.

The basics of running this library are outlined below.

  - Create a Strategy

    - Decide on potential adjustable parameters
    - Create the Indicators you need in the Strategy
    - Write down the logic for entering/exiting the market

  - Create a Cerebro Engine

    - Inject the Strategy (with the parameters of choice)
    - Load and Inject a Data Feed
    - And ... run()
    - Optionally ... plot()

Let's hope you, the user, find the platform useful and fun to work with.

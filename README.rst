backtrader
==========

BackTesting system in Python to test your trading strategies.

As of Jan 15th and with the 1st commit the following is working:

- Creating Indicators
- Creating Strategies
- A basic Broker which accepts "AtMarket" orders (no notification yet)
- Loading Data Feeds from Yahoo Online or from a Yahoo CSV file

  - Indicators provided:
    - MovingAverages: Simple, Exponential, Smoothed, Weighted
    - AverageTrueRange, MACD, RSI, Stochastic
    - Minor Utilities: Highest, Lowest

There are 3 test files under the "tests" directory

  - test.py - Intended to test individual indicators
  - test2.py - Intented to test data feed loading
  - test3.py - Sample reference test strategy to compare to PyAlgoTrade

    test3 is already (broker corrections pending) a fully fledged
    implementation of a strategy.

Some other Python platforms do exist and are actually more complete

  - PyAlgoTrade
  - Zipline
  - Ultra-Finance

Plotting, ratios, event notification and others are already an integral
part of the platforms and you may find them better suited to your
personal needs.

They didn't suit my personal needs and that's how the platform was born
with the following goals

  - Simplicity

    Mostly when creating an indicator and/or strategy. No need to "register"
    to events and even no need to assign output values

    Heavy use of metaclasses is done with this objective in mind.

    This has been mostly achieved even in the first version

  - Speed

    By having not only a quick "tick/bar" based system with no events but
    also by provinding a single-shot calculation for all algorithms.

    Trying to work it out. Collides with simplicity and Elegance

  - Elegance

    In how the calculations for many indicators are laid out just during the
    creation and having a "0"-backwards based system to reference produced/future
    values

    The last value is "0", the previous one is "1" and the next one is "-1"

    This last part and the initial choice of "array.array" are (probably" things
    bound to change if speed must be kept as a goal, specially for one-shot
    calculations to avoid the overhead of Python function calls

  - Flexibility

    Indicators and systems should not be bound to "names" like "Close", "High".

    A MovingAverage of a "lineseries" (for example "close" prices") has nothing
    to do with the regular OHLC bar components.

    This objective has been achieved


The platform is bound to evolve and add many more indicators and sample strategies.

It simply takes time ...
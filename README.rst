
backtrader
==========

.. image:: https://img.shields.io/pypi/v/backtrader.svg
   :target: https://pypi.python.org/pypi/backtrader/
.. image:: https://img.shields.io/pypi/dm/backtrader.svg
   :target: https://pypi.python.org/pypi/backtrader/
.. image:: https://img.shields.io/travis/joyent/backtrader.svg
   :target: https://pypi.python.org/pypi/backtrader/
.. image:: https://img.shields.io/pypi/l/backtrader.svg
   :target: https://github.com/mementum/backtrader/blob/master/LICENSE

BackTesting platform written in Python to test trading strategies.

Read the full documentation at readthedocs.org:

  - `backtrader documentation <http://backtrader.readthedocs.org/en/latest/introduction.html>`_

Installation
============

From pypi:

  - pip install backtrader

  - pip install backtrader[matplotlib]

    If `matplotlib` is not installed and you wish to do some plotting

  - Or run directly from source by placing the *backtrader* directory found in
    the sources inside your project

Features:
=========

  - Bar by Bar (next) operation or batch mode (once) operation
  - Indicators and the addition of any custom end-user developed one
  - Strategies
  - Data Feeds from Online Sources or CSV Files (other forms could be
    implemented)
  - Data Feeds with different timeframes
  - Data Feed Resampling
  - Data Feed Replaying
  - A Broker implementation supporting

    - Commision schemes for stocks and derivatives
    - Orders: AtClose, AtMarket, AtLimit, Stop, StopLimit

  - Position Sizers for the automatic determination of the stake
  - Optimization of Strategies
  - Plotting

Version numbering
=================

X.Y.Z.I

  - X: Major version number. Should stay stable unless something big is changed like an
    overhaul to use numpy
  - Y: Minor version number. To be changed upon adding a complete new feature or
    (god forbids) an incompatible API change.
  - Z: Revision version number. To be changed for documentation updates, small
    changes, small bug fixes
  - I: Number of Indicators already built into the platform

Alternatives
============

If after seeing the docs (see also the example below) you feel this is not your
cup of tea, you can always have a look at similar Python platforms:

  - `PyAlgoTrade <https://github.com/gbeced/pyalgotrade>`_
  - `Zipline <https://github.com/quantopian/zipline>`_
  - `Ultra-Finance <https://code.google.com/p/ultra-finance/>`_
  - `ProfitPy <https://code.google.com/p/profitpy/>`_

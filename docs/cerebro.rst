Cerebro
#######

This class is the cornerstone of ``backtrader`` because it serves as a central
point for:

  Gathering all inputs (Datafeeds), actors (Stragegies), spectators
  (Observers) and critics (Analyzers) and ensures the show still goes on at
  any moment.

A regular usage pattern looks like:

  - Add one or more Datafeeds with ``adddata``

  - Add one or more Strategies (with args and kwargs)

    - ``addstrategy`` for single pass
    - ``optstrategy`` for optimization

  - Add one or more Observers with ``addobserver``

    Cerebro will already add some default ones unless told not to do so)

  - Add one or more Analyzers with ``addanalyzer``

  - Call ``run`` and get the results

  - Look if the strategy is a winner and what the analyzers says


Reference
=========

.. currentmodule:: backtrader

.. autoclass:: Cerebro

   .. automethod:: adddata

   .. automethod:: resampledata

   .. automethod:: replaydata

   .. automethod:: addstrategy

   .. automethod:: optstrategy

   .. automethod:: addobserver

   .. automethod:: addanalyzer

   .. automethod:: addwriter

   .. automethod:: run

   .. automethod:: setbroker

   .. automethod:: getbroker

   .. automethod:: plot

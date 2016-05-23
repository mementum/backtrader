Trade
#####

Definition of a trade:

  - A Trade is open when the a position in a instrument goes from 0 to a size X
    which may positive/negative for long/short positions)

  - A Trade is closed when a position goes from X to 0.

The followig two actions:

  - positive to negative

  - negative to positive

Are actually seen as:

  1. A trade has been closed (position went to 0 from X)

  2. A new trade has been open (position goes from 0 to Y)


Trades are only informative and have no user callable methods.


Reference: Trade
================

.. currentmodule:: backtrader.trade

.. autoclass:: Trade

Position
########

Position on an asset is usually checked from within a Strategy with:

  - ``position`` (a property) or ``getposition(data=None, broker=None)``

    Which will return the position on ``datas[0]`` of the strategy in the
    default ``broker`` provided by cerebro

A position is simply the indication of:

  - An asset is being held with ``size``

  - The average price is ``price``

It serves as a status and can for example be used in deciding if an order has to
be issued or not (example: long positions are only entered if no position is
open)

Reference: Position
===================

.. currentmodule:: backtrader.position

.. autoclass:: Position

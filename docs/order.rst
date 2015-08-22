Orders
######

Orders are used by end user in the following contexts:

  - Creation

    Through Strategy's methods: ``buy`` and ``sell``

  - Cancelation

    Through Strategy's method: ``cancel``

  - Notification

    To Strategy method: ``notify_order``

Order objects are not meant to be manipulated directly, but they can be queried
and the information used (like in the ``BuySell`` observer)


Reference: Order and associated classes
=======================================

.. currentmodule:: backtrader.order

.. autoclass:: Order

.. autoclass:: OrderData

.. autoclass:: OrderExecutionBit

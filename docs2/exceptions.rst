Exceptions
##########

One of the design goals was to quit as early as possible and let the users have
full transparency of what was happening with errors. With the goal to force
oneself to have code that would break on exceptions and forced revisiting the
affected part.

But the time has come and some exceptions may slowly get added to the platform.

Hierarcy
********

The base class for all exceptions is ``BacktraderError`` (which is a direct
subclass of ``Exception``)

Location
********

  1. Inside the module ``errors`` which can be reached as in for example::

       import backtrader as bt

       class Stratetgy(bt.Strategy):

           def __init__(self):
	       if something_goes_wrong():
	           raise bt.errors.StrategySkipError

  2. Directly from ``backtrader`` as in::

       import backtrader as bt

       class Stratetgy(bt.Strategy):

           def __init__(self):
	       if something_goes_wrong():
	           raise StrategySkipError

Exceptions
**********

``StrategySkipError``
+++++++++++++++++++++

Requests the platform to skip this strategy for backtesting. To be raised
during the initialization (``__init__``) phase of the instance


User Defined Commissions
------------------------

The most important part of reworking the CommInfo object to the actual
incarnation involved:

  - Retaining the original ``CommissionInfo`` class and behavior

  - Opening the door for easy creation of user defined commissions

  - Making the format xx% the default for new commission schemes instead of 0.xx
    (just a matter of taste), keeping the behavior configurable

.. note:: See below he docstring of ``CommInfoBase`` for parameters reference

Defining a Commission Scheme
++++++++++++++++++++++++++++

It involves 1 or 2 steps

  1. Subclassing ``CommInfoBase``

     Simply changing the default parameters may be enough. ``backtrader``
     already does this with some definitions present in the module
     ``backtrader.commissions``. The regular industry standard for Futures is a
     fixed amount per contract and per round. The definition can be done as::

      class CommInfo_Futures_Fixed(CommInfoBase):
          params = (
              ('stocklike', False),
              ('commtype', CommInfoBase.COMM_FIXED),
          )

     For stocks and perc-wise commissions::

      class CommInfo_Stocks_Perc(CommInfoBase):
          params = (
              ('stocklike', True),
              ('commtype', CommInfoBase.COMM_PERC),
          )

     As stated above the default for the interpretation of the percentage here
     (passed as parameter ``commission``) is that of: **xx%**. Should the
     old/other behavior be wished **0.xx**, it can be easily done::

      class CommInfo_Stocks_PercAbs(CommInfoBase):
          params = (
              ('stocklike', True),
              ('commtype', CommInfoBase.COMM_PERC),
              ('percabs', True),
          )

  2. Overriding (if needed be) the ``_getcommission`` method

     Defined as::

       def _getcommission(self, size, price, pseudoexec):
          '''Calculates the commission of an operation at a given price

          pseudoexec: if True the operation has not yet been executed
          '''

     More details in a practical example below

How to apply this to the platform
+++++++++++++++++++++++++++++++++

Once a ``CommInfoBase`` subclass is in place the trick is to use
``broker.addcommission`` rather than the usual ``broker.setcommission``. The
latter will internally use the legacy ``CommissionInfoObject``.

Easier done than said::

  ...

  comminfo = CommInfo_Stocks_PercAbs(commission=0.005)  # 0.5%
  cerebro.broker.addcommission(comminfo)

The ``addcommission`` method is defined as follows::

  def addcommissioninfo(self, comminfo, name=None):
      self.comminfo[name] = comminfo

Setting ``name`` means that the ``comminfo`` object will only apply to assets
with that name. The default value of ``None`` means it applies to all assets in
the system.

A practical example
+++++++++++++++++++

`Ticket #45 <https://github.com/mementum/backtrader/issues/45>`_ asks about a
commission scheme which applies to Futures, is percentage wise and uses the
commission percentage on the entire "virtual" value of the contract. ie:
includes the future multiplier in the commission calculation.

It should be easy::

  import backtrader as bt

  class CommInfo_Fut_Perc_Mult(bt.CommInfoBase):
      params = (
        ('stocklike', False),  # Futures
        ('commtype', bt.CommInfoBase.COMM_PERC),  # Apply % Commission
      # ('percabs', False),  # pass perc as xx% which is the default
      )

      def _getcommission(self, size, price, pseudoexec):
          return size * price * self.p.commission * self.p.mult

Putting it into the system::

  comminfo = CommInfo_Fut_Perc_Mult(
      commission=0.1,  # 0.1%
      mult=10,
      margin=2000  # Margin is needed for futures-like instruments
  )

  cerebro.addcommission(comminfo)

If the format **0.xx** is preferred as the default, just set param ``percabs``
to ``True``::

  class CommInfo_Fut_Perc_Mult(bt.CommInfoBase):
      params = (
        ('stocklike', False),  # Futures
        ('commtype', bt.CommInfoBase.COMM_PERC),  # Apply % Commission
        ('percabs', True),  # pass perc as 0.xx
      )

  comminfo = CommInfo_Fut_Perc_Mult(
      commission=0.001,  # 0.1%
      mult=10,
      margin=2000  # Margin is needed for futures-like instruments
  )

  cerebro.addcommission(comminfo)

This all should do the trick.

Explaining ``pseudoexec``
+++++++++++++++++++++++++

Let's recall the definition of ``_getcommission``::

  def _getcommission(self, size, price, pseudoexec):
      '''Calculates the commission of an operation at a given price

      pseudoexec: if True the operation has not yet been executed
      '''

The purpose of the ``pseudoexec`` arg may seem obscure but it serves a purpose.

  - The platform may call this method to do precalculation of available cash and
    some other tasks

  - This means that the method may (and it actually will) be called more than
    once with the same parameters

``pseudoexec`` indicates whether the call corresponds to the actual execution of
an order. Although at first sight this may not seem "relevant" it is if
scenarios like the following are considered:

  - A broker offers a 50% discount on futures round-trip commission once the
    amount of negotiated contracts has exceeeded 5000 units

    In such case and if ``pseudoexec`` was not there, the multiple non-execution
    calls to the method would quickly trigger the assumption that the discount
    is in place.

Putting the scenario to work::

  import backtrader as bt

  class CommInfo_Fut_Discount(bt.CommInfoBase):
      params = (
        ('stocklike', False),  # Futures
        ('commtype', bt.CommInfoBase.COMM_FIXED),  # Apply Commission

        # Custom params for the discount
	('discount_volume', 5000),  # minimum contracts to achieve discount
	('discount_perc', 50.0),  # 50.0% discount
      )

      negotiated_volume = 0  # attribute to keep track of the actual volume

      def _getcommission(self, size, price, pseudoexec):
          if self.negotiated_volume > self.p.discount_volume:
	     actual_discount = self.p.discount_perc / 100.0
	  else:
	     actual_discount = 0.0

	  commission = self.p.commission * (1.0 - actual_discount)
	  commvalue = size * price * commission

	  if not pseudoexec:
	     # keep track of actual real executed size for future discounts
	     self.negotiated_volume += size

	  return commvalue

The purpose and being of ``pseudoexec`` are hopefully clear now.


CommInfoBase docstring and params
+++++++++++++++++++++++++++++++++

Here it is::

  class CommInfoBase(with_metaclass(MetaParams)):
      '''Base Class for the Commission Schemes.

      Params:

        - commission (def: 0.0): base commission value in percentage or monetary
          units

        - mult (def 1.0): multiplier applied to the asset for value/profit

        - margin (def: None): amount of monetary units needed to open/hold an
          operation. It only applies if the final ``_stocklike`` attribute in the
          class is set to False

        - commtype (def: None): Supported values are CommInfoBase.COMM_PERC
          (commission to be understood as %) and CommInfoBase.COMM_FIXED
          (commission to be understood as monetary units)

          The default value of ``None`` is a supported value to retain
          compatibility with the legacy ``CommissionInfo`` object. If
          ``commtype`` is set to None, then the following applies:

            - margin is None: Internal _commtype is set to COMM_PERC and
              _stocklike is set to True (Operating %-wise with Stocks)

            - margin is not None: _commtype set to COMM_FIXED and _stocklike set
              to False (Operating with fixed rount-trip commission with Futures)

          If this param is set to something else than None, then it will be
          passed to the internal ``_commtype`` attribute and the same will be
          done with the param ``stocklike`` and the internal attribute
          ``_stocklike``

        - stocklike (def: False):  Indicates if the instrument is Stock-like or
          Futures-like (see the ``commtype`` discussion above)

        - percabs (def: False): when ``commtype`` is set to COMM_PERC, whether
          the parameter ``commission`` has to be understood as XX% or 0.XX

          If this param is True: 0.XX
          If this param is False: XX%

      Attributes:

        - _stocklike: Final value to use for Stock-like/Futures-like behavior
        - _commtype: Final value to use for PERC vs FIXED commissions

        This two are used internally instead of the declared params to enable the
        compatibility check described above for the legacy ``CommissionInfo``
        object
      '''

      COMM_PERC, COMM_FIXED = range(2)

      params = (
          ('commission', 0.0), ('mult', 1.0), ('margin', None),
          ('commtype', None),
          ('stocklike', False),
          ('percabs', False),
      )

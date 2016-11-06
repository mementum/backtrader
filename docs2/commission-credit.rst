Commissions: Credit
###################

In some situations, the cash amount in real brokers may be decreased because
the operation on assets includes an interest rate. Examples:

  - Short selling of stocks

  - ETFs both long and short

The charge goes directly against the cash balance in the broker account. But it
can still be seen as part of a commission scheme. And as such it has been
modeled in *backtrader*.

The ``CommInfoBase`` class (and with it also the ``CommissionInfo`` main
interface object) has been extended with:

  - Two (2) new parameters that allow setting the interest rate and
    determining if should be applied only to the short side or to both long and
    short

Parameters
**********

  - ``interest`` (def: ``0.0``)

    If this is non-zero, this is the yearly interest charged for holding a
    short selling position. This is mostly meant for stock short-selling

    The default formula applied: ``days * price * size * (interest / 365)``

    It must be specified in absolute terms: 0.05 -> 5%

    .. note:: the behavior can be changed by overriding the method:
             ``get_credit_interest``

  - ``interest_long`` (def: ``False``)

    Some products like ETFs get charged on interest for short and long
    positions. If ths is ``True`` and ``interest`` is non-zero the interest
    will be charged on both directions


The formula
***********

The default implementation will use the following formula::

  days * abs(size) * price * (interest / 365)

Where:

  - ``days``: number of days elapsed since position was opened or the last
    credit interest calculation took place


Overriding the formula
**********************

In order to change the formula subclassing of ``CommissionInfo`` is needed. The
method to be overridden is::

    def _get_credit_interest(self, size, price, days, dt0, dt1):
        '''
        This method returns  the cost in terms of credit interest charged by
        the broker.

        In the case of ``size > 0`` this method will only be called if the
        parameter to the class ``interest_long`` is ``True``

        The formulat for the calculation of the credit interest rate is:

          The formula: ``days * price * abs(size) * (interest / 365)``


        Params:
          - ``data``: data feed for which interest is charged

          - ``size``: current position size. > 0 for long positions and < 0 for
            short positions (this parameter will not be ``0``)

          - ``price``: current position price

          - ``days``: number of days elapsed since last credit calculation
            (this is (dt0 - dt1).days)

          - ``dt0``: (datetime.datetime) current datetime

          - ``dt1``: (datetime.datetime) datetime of previous calculation

        ``dt0`` and ``dt1`` are not used in the default implementation and are
        provided as extra input for overridden methods
        '''

It might be that the *broker* doesn't consider weekends or bank holidays when
calculating the interest rate. In this case this subclass would do the trick
::

   import backtrader as bt

   class MyCommissionInfo(bt.CommInfo):

      def _get_credit_interest(self, size, price, days, dt0, dt1):
          return 1.0 * abs(size) * price * (self.p.interest / 365.0)

In this case, in the formula:

    - ``days`` has been replaced by ``1.0``

Because if weekends/bank holidays do not count, the next calculation will
always happen ``1`` trading da after the previous calculation

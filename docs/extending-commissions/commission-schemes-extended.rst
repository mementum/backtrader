
Extending Commissions
---------------------

Commissions and asociated functionality were managed by a single class
``CommissionInfo`` which was mostly instantiated by calling
``broker.setcommission``.

The concept was limited to futures with margin and a fixed commission per
contract and stocks with a price/size percentage based commission. Not the most
flexible of schemes even if it has served its purpose.

A request for enhancement on GitHub `#29
<https://github.com/mementum/backtrader/issues/29>`_ led to some rework in
order to:

  - Keep ``CommissionInfo`` and ``broker.setcommission`` compatible with the
    original behavior

  - Do some clean up of the code

  - Make the Commission scheme flexible to support the enhancement request and
    further possibilities

The actual work before getting to the sample

.. code-block:: python

    class CommInfoBase(with_metaclass(MetaParams)):
        COMM_PERC, COMM_FIXED = range(2)

        params = (
            ('commission', 0.0), ('mult', 1.0), ('margin', None),
            ('commtype', None),
            ('stocklike', False),
            ('percabs', False),
        )

A base class for ``CommissionInfo`` has been introduced which add new parameters
to the mix:

  - ``commtype`` (default: ``None``)

    This is the key to compatibility. If the value is ``None``, the behavior of
    the ``CommissionInfo`` object and ``broker.setcommission`` will work as
    before. Being that:

      - If ``margin`` is set then the commission scheme is for futures with a
	fixed commission per contract

      - If ``margin`` is not set, the commission scheme is for stocks with a
	percentage based approach

    If the value is ``COMM_PERC`` or ``COMM_FIXED`` (or any other from derived
    classes) this obviously decides if the commission if fixed or percent based

  - ``stocklike`` (default: ``False``)

    As explained above, the actual behavior in the old ``CommissionInfo`` object
    is determined by the parameter ``margin``

    As above if ``commtype`` is set to something else than ``None``, then this
    value indicates whether the asset is a futures-like asset (margin will be
    used and bar based cash adjustment will be performed9 or else this a
    stocks-like asset

  - ``percabs`` (default: ``False``)

    If ``False`` then the percentage must be passed in relative terms (xx%)

    If ``True`` the percentage has to be passed as an absolute value (0.xx)

    ``CommissionInfo`` is subclassed from ``CommInfoBase`` changing the default
    value of this parameter to ``True`` to keep the compatible behavior

All these parameters can also be used in ``broker.setcommission`` which now
looks like this::

    def setcommission(self,
                      commission=0.0, margin=None, mult=1.0,
                      commtype=None, percabs=True, stocklike=False,
                      name=None):

Notice the following:

  - ``percabs`` is ``True`` to keep the behavior compatible with the old call as
    mentioned above for the ``CommissionInfo`` object

The old sample to test ``commissions-schemes`` has been reworked to support
command line arguments and the new behavior. The usage help::

    $ ./commission-schemes.py --help
    usage: commission-schemes.py [-h] [--data DATA] [--fromdate FROMDATE]
                                 [--todate TODATE] [--stake STAKE]
                                 [--period PERIOD] [--cash CASH] [--comm COMM]
                                 [--mult MULT] [--margin MARGIN]
                                 [--commtype {none,perc,fixed}] [--stocklike]
                                 [--percrel] [--plot] [--numfigs NUMFIGS]

    Commission schemes

    optional arguments:
      -h, --help            show this help message and exit
      --data DATA, -d DATA  data to add to the system (default:
                            ../../datas/2006-day-001.txt)
      --fromdate FROMDATE, -f FROMDATE
                            Starting date in YYYY-MM-DD format (default:
                            2006-01-01)
      --todate TODATE, -t TODATE
                            Starting date in YYYY-MM-DD format (default:
                            2006-12-31)
      --stake STAKE         Stake to apply in each operation (default: 1)
      --period PERIOD       Period to apply to the Simple Moving Average (default:
                            30)
      --cash CASH           Starting Cash (default: 10000.0)
      --comm COMM           Commission factor for operation, either apercentage or
                            a per stake unit absolute value (default: 2.0)
      --mult MULT           Multiplier for operations calculation (default: 10)
      --margin MARGIN       Margin for futures-like operations (default: 2000.0)
      --commtype {none,perc,fixed}
                            Commission - choose none for the old CommissionInfo
                            behavior (default: none)
      --stocklike           If the operation is for stock-like assets orfuture-
                            like assets (default: False)
      --percrel             If perc is expressed in relative xx{'const': True,
                            'help': u'If perc is expressed in relative xx%
                            ratherthan absolute value 0.xx', 'option_strings': [u'
                            --percrel'], 'dest': u'percrel', 'required': False,
                            'nargs': 0, 'choices': None, 'default': False, 'prog':
                            'commission-schemes.py', 'container':
                            <argparse._ArgumentGroup object at
                            0x0000000007EC9828>, 'type': None, 'metavar':
                            None}atherthan absolute value 0.xx (default: False)
      --plot, -p            Plot the read data (default: False)
      --numfigs NUMFIGS, -n NUMFIGS
                            Plot using numfigs figures (default: 1)


Let's do some runs to recreate the original behavior of the original commission
schemes posts.

Commissions for futures (fixed and with margin)
===============================================

The execution and chart::

    $ ./commission-schemes.py --comm 2.0 --margin 2000.0 --mult 10 --plot


.. thumbnail:: ./commission-futures-extended.png

And the output showing a fixed commission of 2.0 monetary units (default stake
is 1)::

    2006-03-09, BUY CREATE, 3757.59
    2006-03-10, BUY EXECUTED, Price: 3754.13, Cost: 2000.00, Comm 2.00
    2006-04-11, SELL CREATE, 3788.81
    2006-04-12, SELL EXECUTED, Price: 3786.93, Cost: 2000.00, Comm 2.00
    2006-04-12, TRADE PROFIT, GROSS 328.00, NET 324.00
    ...

Commissions for stocks (perc and withoout  margin)
==================================================

The execution and chart::

    $ ./commission-schemes.py --comm 0.005 --margin 0 --mult 1 --plot


.. thumbnail:: ./commission-stocks-extended.png

To improve readability a relative % value can be used::

    $ ./commission-schemes.py --percrel --comm 0.5 --margin 0 --mult 1 --plot

Now ``0.5`` means directly ``0.5%``

Being the output in both cases::

    2006-03-09, BUY CREATE, 3757.59
    2006-03-10, BUY EXECUTED, Price: 3754.13, Cost: 3754.13, Comm 18.77
    2006-04-11, SELL CREATE, 3788.81
    2006-04-12, SELL EXECUTED, Price: 3786.93, Cost: 3754.13, Comm 18.93
    2006-04-12, TRADE PROFIT, GROSS 32.80, NET -4.91
    ...

Commissions for futures (perc and with margin)
==============================================

Using the new parameters, futures on a perc based scheme::

    $ ./commission-schemes.py --commtype perc --percrel --comm 0.5 --margin 2000 --mult 10 --plot

.. thumbnail:: ./commission-stocks-extended.png

It should come to no surprise that by changing the commission ... the final
result has changed

The output shows that the commission is variable now::

    2006-03-09, BUY CREATE, 3757.59
    2006-03-10, BUY EXECUTED, Price: 3754.13, Cost: 2000.00, Comm 18.77
    2006-04-11, SELL CREATE, 3788.81
    2006-04-12, SELL EXECUTED, Price: 3786.93, Cost: 2000.00, Comm 18.93
    2006-04-12, TRADE PROFIT, GROSS 328.00, NET 290.29
    ...

Being in the previous run set a 2.0 monetary units (for the default stake of 1)

Another post will details the new classes and the implementation of a homme
cooked commission scheme.

The code for the sample
=======================

.. literalinclude:: ./commission-schemes-extended.py
   :language: python
   :lines: 21-

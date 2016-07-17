
Pyfolio Integration
###################

The integration of a *portfolio* tool, namely ``pyfolio``, came up with in
`Ticket #108 <https://github.com/mementum/backtrader/issues/108>`_.

A first look at the tutorial deemed it as difficult, given the tight
integration amongst ``zipline`` and ``pyfolio``, but the sample *test* data
available with ``pyfolio`` for some other uses is actually pretty useful to
decode what's running behind the scenes and hence the wonder of integration.

Most of the pieces were already in-place in *backtrader*:

  - Analyzer infrastructure
  - Children analyzer
  - A TimeReturn analyzer

Only a main ``PyFolio`` analyzer and 3 easy *children* analyzer are
needed. Plus a method that relies on one of the dependencies already needed by
``pyfolio`` which is ``pandas``.

The most challenging part ... "getting all the dependencies right".

  - Update of ``pandas``
  - Update of ``numpy``
  - Update of ``scikit-lean``
  - Update of ``seaborn``

Under Unix-like environments with a *C* compiler it's all about time. Under
Windows and even with the specific *Microsoft* compiler installed (in this case
the chain for *Python 2.7*) things failed. But a well known site with a
collection of up-to-date packages for *Windows* helped. Visit it if you ever
need it:

  - http://www.lfd.uci.edu/~gohlke/pythonlibs/

The integration wouldn't be complete if it wasn't tested and that's why the
usual sample is as always present.

No PyFolio
==========

The sample uses ``random.randint`` to decide when to *buy*/*sell*, so this is
simply a check that things are working::

  $ ./pyfoliotest.py --printout --no-pyfolio --plot

Output::

  Len,Datetime,Open,High,Low,Close,Volume,OpenInterest
  0001,2005-01-03T23:59:59,38.36,38.90,37.65,38.18,25482800.00,0.00
  BUY  1000 @%23.58
  0002,2005-01-04T23:59:59,38.45,38.54,36.46,36.58,26625300.00,0.00
  BUY  1000 @%36.58
  SELL 500 @%22.47
  0003,2005-01-05T23:59:59,36.69,36.98,36.06,36.13,18469100.00,0.00
  ...
  SELL 500 @%37.51
  0502,2006-12-28T23:59:59,25.62,25.72,25.30,25.36,11908400.00,0.00
  0503,2006-12-29T23:59:59,25.42,25.82,25.33,25.54,16297800.00,0.00
  SELL 250 @%17.14
  SELL 250 @%37.01

.. thumbnail:: sample-run-no-pyfolio.png

There a 3 datas and several *buy* and *sell* operations are randomly chosen and
scattered over the 2 year default life of the test run

A PyFolio run
=============

``pyfolio`` things work well when running inside a *Jupyter Notebook* including
inline plotting. Here is the *notebook*

.. note:: ``runstrat`` gets here `[]` as argument to run with default arguments
	  and skip arguments passed by the *notebook* itself



.. code:: python

    %matplotlib inline

.. code:: python

    from __future__ import (absolute_import, division, print_function,
                            unicode_literals)


    import argparse
    import datetime
    import random

    import backtrader as bt


    class St(bt.Strategy):
        params = (
            ('printout', False),
            ('stake', 1000),
        )

        def __init__(self):
            pass

        def start(self):
            if self.p.printout:
                txtfields = list()
                txtfields.append('Len')
                txtfields.append('Datetime')
                txtfields.append('Open')
                txtfields.append('High')
                txtfields.append('Low')
                txtfields.append('Close')
                txtfields.append('Volume')
                txtfields.append('OpenInterest')
                print(','.join(txtfields))

        def next(self):
            if self.p.printout:
                # Print only 1st data ... is just a check that things are running
                txtfields = list()
                txtfields.append('%04d' % len(self))
                txtfields.append(self.data.datetime.datetime(0).isoformat())
                txtfields.append('%.2f' % self.data0.open[0])
                txtfields.append('%.2f' % self.data0.high[0])
                txtfields.append('%.2f' % self.data0.low[0])
                txtfields.append('%.2f' % self.data0.close[0])
                txtfields.append('%.2f' % self.data0.volume[0])
                txtfields.append('%.2f' % self.data0.openinterest[0])
                print(','.join(txtfields))

            # Data 0
            for data in self.datas:
                toss = random.randint(1, 10)
                curpos = self.getposition(data)
                if curpos.size:
                    if toss > 5:
                        size = curpos.size // 2
                        self.sell(data=data, size=size)
                        if self.p.printout:
                            print('SELL {} @%{}'.format(size, data.close[0]))

                elif toss < 5:
                    self.buy(data=data, size=self.p.stake)
                    if self.p.printout:
                        print('BUY  {} @%{}'.format(self.p.stake, data.close[0]))


    def runstrat(args=None):
        args = parse_args(args)

        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(args.cash)

        dkwargs = dict()
        if args.fromdate:
            fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
            dkwargs['fromdate'] = fromdate

        if args.todate:
            todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
            dkwargs['todate'] = todate

        data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **dkwargs)
        cerebro.adddata(data0, name='Data0')

        data1 = bt.feeds.BacktraderCSVData(dataname=args.data1, **dkwargs)
        cerebro.adddata(data1, name='Data1')

        data2 = bt.feeds.BacktraderCSVData(dataname=args.data2, **dkwargs)
        cerebro.adddata(data2, name='Data2')

        cerebro.addstrategy(St, printout=args.printout)
        if not args.no_pyfolio:
            cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

        results = cerebro.run()
        if not args.no_pyfolio:
            strat = results[0]
            pyfoliozer = strat.analyzers.getbyname('pyfolio')

            returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
            if args.printout:
                print('-- RETURNS')
                print(returns)
                print('-- POSITIONS')
                print(positions)
                print('-- TRANSACTIONS')
                print(transactions)
                print('-- GROSS LEVERAGE')
                print(gross_lev)

            import pyfolio as pf
            pf.create_full_tear_sheet(
                returns,
                positions=positions,
                transactions=transactions,
                gross_lev=gross_lev,
                live_start_date='2005-05-01',
                round_trips=True)

        if args.plot:
            cerebro.plot(style=args.plot_style)


    def parse_args(args=None):

        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description='Sample for pivot point and cross plotting')

        parser.add_argument('--data0', required=False,
                            default='../../datas/yhoo-1996-2015.txt',
                            help='Data to be read in')

        parser.add_argument('--data1', required=False,
                            default='../../datas/orcl-1995-2014.txt',
                            help='Data to be read in')

        parser.add_argument('--data2', required=False,
                            default='../../datas/nvda-1999-2014.txt',
                            help='Data to be read in')

        parser.add_argument('--fromdate', required=False,
                            default='2005-01-01',
                            help='Starting date in YYYY-MM-DD format')

        parser.add_argument('--todate', required=False,
                            default='2006-12-31',
                            help='Ending date in YYYY-MM-DD format')

        parser.add_argument('--printout', required=False, action='store_true',
                            help=('Print data lines'))

        parser.add_argument('--cash', required=False, action='store',
                            type=float, default=50000,
                            help=('Cash to start with'))

        parser.add_argument('--plot', required=False, action='store_true',
                            help=('Plot the result'))

        parser.add_argument('--plot-style', required=False, action='store',
                            default='bar', choices=['bar', 'candle', 'line'],
                            help=('Plot style'))

        parser.add_argument('--no-pyfolio', required=False, action='store_true',
                            help=('Do not do pyfolio things'))

        import sys
        aargs = args if args is not None else sys.argv[1:]
        return parser.parse_args(aargs)

.. code:: python

    runstrat([])


.. parsed-literal::

    Entire data start date: 2005-01-03
    Entire data end date: 2006-12-29


    Out-of-Sample Months: 20
    Backtest Months: 3



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Performance statistics</th>
          <th>All history</th>
          <th>Backtest</th>
          <th>Out of sample</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>annual_return</th>
          <td>0.06</td>
          <td>-0.05</td>
          <td>0.08</td>
        </tr>
        <tr>
          <th>annual_volatility</th>
          <td>0.09</td>
          <td>0.09</td>
          <td>0.10</td>
        </tr>
        <tr>
          <th>sharpe_ratio</th>
          <td>0.62</td>
          <td>-0.55</td>
          <td>0.83</td>
        </tr>
        <tr>
          <th>calmar_ratio</th>
          <td>0.78</td>
          <td>-1.13</td>
          <td>1.09</td>
        </tr>
        <tr>
          <th>stability_of_timeseries</th>
          <td>0.75</td>
          <td>-0.47</td>
          <td>0.70</td>
        </tr>
        <tr>
          <th>max_drawdown</th>
          <td>-0.07</td>
          <td>-0.04</td>
          <td>-0.07</td>
        </tr>
        <tr>
          <th>omega_ratio</th>
          <td>1.16</td>
          <td>0.88</td>
          <td>1.22</td>
        </tr>
        <tr>
          <th>sortino_ratio</th>
          <td>0.97</td>
          <td>-0.76</td>
          <td>1.33</td>
        </tr>
        <tr>
          <th>skew</th>
          <td>1.24</td>
          <td>0.35</td>
          <td>1.37</td>
        </tr>
        <tr>
          <th>kurtosis</th>
          <td>12.72</td>
          <td>5.66</td>
          <td>13.59</td>
        </tr>
        <tr>
          <th>tail_ratio</th>
          <td>0.87</td>
          <td>0.46</td>
          <td>0.91</td>
        </tr>
        <tr>
          <th>common_sense_ratio</th>
          <td>0.91</td>
          <td>0.43</td>
          <td>0.98</td>
        </tr>
        <tr>
          <th>information_ratio</th>
          <td>-0.02</td>
          <td>0.03</td>
          <td>-0.04</td>
        </tr>
        <tr>
          <th>alpha</th>
          <td>0.03</td>
          <td>-0.02</td>
          <td>0.03</td>
        </tr>
        <tr>
          <th>beta</th>
          <td>0.31</td>
          <td>0.25</td>
          <td>0.33</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Worst Drawdown Periods</th>
          <th>net drawdown in %</th>
          <th>peak date</th>
          <th>valley date</th>
          <th>recovery date</th>
          <th>duration</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>7.06</td>
          <td>2005-07-11</td>
          <td>2006-04-17</td>
          <td>2006-05-24</td>
          <td>228</td>
        </tr>
        <tr>
          <th>1</th>
          <td>5.53</td>
          <td>2005-02-18</td>
          <td>2005-05-11</td>
          <td>2005-05-16</td>
          <td>62</td>
        </tr>
        <tr>
          <th>2</th>
          <td>3.33</td>
          <td>2006-07-03</td>
          <td>2006-07-13</td>
          <td>2006-09-21</td>
          <td>59</td>
        </tr>
        <tr>
          <th>3</th>
          <td>2.11</td>
          <td>2006-09-25</td>
          <td>2006-10-03</td>
          <td>2006-10-24</td>
          <td>22</td>
        </tr>
        <tr>
          <th>4</th>
          <td>2.11</td>
          <td>2006-10-31</td>
          <td>2006-12-07</td>
          <td>2006-12-19</td>
          <td>36</td>
        </tr>
      </tbody>
    </table>
    </div>


.. parsed-literal::



    [-0.012 -0.025]



.. thumbnail:: output_2_4.png



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Stress Events</th>
          <th>mean</th>
          <th>min</th>
          <th>max</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Low Volatility Bull Market</th>
          <td>0.02%</td>
          <td>-2.68%</td>
          <td>4.85%</td>
        </tr>
      </tbody>
    </table>
    </div>



.. thumbnail:: output_2_6.png



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Top 10 long positions of all time</th>
          <th>max</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Data2</th>
          <td>93.59%</td>
        </tr>
        <tr>
          <th>Data0</th>
          <td>80.42%</td>
        </tr>
        <tr>
          <th>Data1</th>
          <td>34.47%</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Top 10 short positions of all time</th>
          <th>max</th>
        </tr>
      </thead>
      <tbody>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Top 10 positions of all time</th>
          <th>max</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Data2</th>
          <td>93.59%</td>
        </tr>
        <tr>
          <th>Data0</th>
          <td>80.42%</td>
        </tr>
        <tr>
          <th>Data1</th>
          <td>34.47%</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>All positions ever held</th>
          <th>max</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Data2</th>
          <td>93.59%</td>
        </tr>
        <tr>
          <th>Data0</th>
          <td>80.42%</td>
        </tr>
        <tr>
          <th>Data1</th>
          <td>34.47%</td>
        </tr>
      </tbody>
    </table>
    </div>



.. thumbnail:: output_2_11.png


.. parsed-literal::

    D:\dro\bin\WinPython-64bit-2.7.10.3\python-2.7.10.amd64\lib\site-packages\pyfolio\plotting.py:1210: FutureWarning: .resample() is now a deferred operation
    use .resample(...).mean() instead of .resample(...)
      \*\*kwargs)



.. thumbnail:: output_2_13.png



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Summary stats</th>
          <th>All trades</th>
          <th>Long trades</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Total number of round_trips</th>
          <td>661.00</td>
          <td>661.00</td>
        </tr>
        <tr>
          <th>Percent profitable</th>
          <td>0.53</td>
          <td>0.53</td>
        </tr>
        <tr>
          <th>Winning round_trips</th>
          <td>350.00</td>
          <td>350.00</td>
        </tr>
        <tr>
          <th>Losing round_trips</th>
          <td>305.00</td>
          <td>305.00</td>
        </tr>
        <tr>
          <th>Even round_trips</th>
          <td>6.00</td>
          <td>6.00</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>PnL stats</th>
          <th>All trades</th>
          <th>Long trades</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Total profit</th>
          <td>$5675.87</td>
          <td>$5675.87</td>
        </tr>
        <tr>
          <th>Gross profit</th>
          <td>$21571.73</td>
          <td>$21571.73</td>
        </tr>
        <tr>
          <th>Gross loss</th>
          <td>$-15895.86</td>
          <td>$-15895.86</td>
        </tr>
        <tr>
          <th>Profit factor</th>
          <td>$1.36</td>
          <td>$1.36</td>
        </tr>
        <tr>
          <th>Avg. trade net profit</th>
          <td>$8.59</td>
          <td>$8.59</td>
        </tr>
        <tr>
          <th>Avg. winning trade</th>
          <td>$61.63</td>
          <td>$61.63</td>
        </tr>
        <tr>
          <th>Avg. losing trade</th>
          <td>$-52.12</td>
          <td>$-52.12</td>
        </tr>
        <tr>
          <th>Ratio Avg. Win:Avg. Loss</th>
          <td>$1.18</td>
          <td>$1.18</td>
        </tr>
        <tr>
          <th>Largest winning trade</th>
          <td>$1024.99</td>
          <td>$1024.99</td>
        </tr>
        <tr>
          <th>Largest losing trade</th>
          <td>$-1155.00</td>
          <td>$-1155.00</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Duration stats</th>
          <th>All trades</th>
          <th>Long trades</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Avg duration</th>
          <td>17 days 00:00:00.001512</td>
          <td>17 days 00:00:00.001512</td>
        </tr>
        <tr>
          <th>Median duration</th>
          <td>16 days 00:00:00</td>
          <td>16 days 00:00:00</td>
        </tr>
        <tr>
          <th>Avg # round_trips per day</th>
          <td>11.80</td>
          <td>11.80</td>
        </tr>
        <tr>
          <th>Avg # round_trips per month</th>
          <td>247.88</td>
          <td>247.88</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Return stats</th>
          <th>All trades</th>
          <th>Long trades</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Avg returns all round_trips</th>
          <td>0.02%</td>
          <td>0.02%</td>
        </tr>
        <tr>
          <th>Avg returns winning</th>
          <td>0.12%</td>
          <td>0.12%</td>
        </tr>
        <tr>
          <th>Avg returns losing</th>
          <td>-0.10%</td>
          <td>-0.10%</td>
        </tr>
        <tr>
          <th>Median returns all round_trips</th>
          <td>0.00%</td>
          <td>0.00%</td>
        </tr>
        <tr>
          <th>Median returns winning</th>
          <td>0.02%</td>
          <td>0.02%</td>
        </tr>
        <tr>
          <th>Median returns losing</th>
          <td>-0.02%</td>
          <td>-0.02%</td>
        </tr>
        <tr>
          <th>Largest winning trade</th>
          <td>2.11%</td>
          <td>2.11%</td>
        </tr>
        <tr>
          <th>Largest losing trade</th>
          <td>-2.37%</td>
          <td>-2.37%</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Symbol stats</th>
          <th>Data0</th>
          <th>Data1</th>
          <th>Data2</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Avg returns all round_trips</th>
          <td>-0.02%</td>
          <td>0.01%</td>
          <td>0.06%</td>
        </tr>
        <tr>
          <th>Avg returns winning</th>
          <td>0.12%</td>
          <td>0.05%</td>
          <td>0.19%</td>
        </tr>
        <tr>
          <th>Avg returns losing</th>
          <td>-0.14%</td>
          <td>-0.04%</td>
          <td>-0.14%</td>
        </tr>
        <tr>
          <th>Median returns all round_trips</th>
          <td>-0.00%</td>
          <td>0.00%</td>
          <td>0.01%</td>
        </tr>
        <tr>
          <th>Median returns winning</th>
          <td>0.03%</td>
          <td>0.01%</td>
          <td>0.05%</td>
        </tr>
        <tr>
          <th>Median returns losing</th>
          <td>-0.02%</td>
          <td>-0.01%</td>
          <td>-0.04%</td>
        </tr>
        <tr>
          <th>Largest winning trade</th>
          <td>1.91%</td>
          <td>0.71%</td>
          <td>2.11%</td>
        </tr>
        <tr>
          <th>Largest losing trade</th>
          <td>-2.37%</td>
          <td>-0.64%</td>
          <td>-0.99%</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <div>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th>Profitability (PnL / PnL total) per name</th>
          <th>pnl</th>
        </tr>
        <tr>
          <th>symbol</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>Data2</th>
          <td>1.11%</td>
        </tr>
        <tr>
          <th>Data1</th>
          <td>0.14%</td>
        </tr>
        <tr>
          <th>Data0</th>
          <td>-0.25%</td>
        </tr>
      </tbody>
    </table>
    </div>



.. parsed-literal::

    <matplotlib.figure.Figure at 0x23982b70>



.. thumbnail:: output_2_21.png


Usage of the sample::

  $ ./pyfoliotest.py --help
  usage: pyfoliotest.py [-h] [--data0 DATA0] [--data1 DATA1] [--data2 DATA2]
                        [--fromdate FROMDATE] [--todate TODATE] [--printout]
                        [--cash CASH] [--plot] [--plot-style {bar,candle,line}]
                        [--no-pyfolio]

  Sample for pivot point and cross plotting

  optional arguments:
    -h, --help            show this help message and exit
    --data0 DATA0         Data to be read in (default:
                          ../../datas/yhoo-1996-2015.txt)
    --data1 DATA1         Data to be read in (default:
                          ../../datas/orcl-1995-2014.txt)
    --data2 DATA2         Data to be read in (default:
                          ../../datas/nvda-1999-2014.txt)
    --fromdate FROMDATE   Starting date in YYYY-MM-DD format (default:
                          2005-01-01)
    --todate TODATE       Ending date in YYYY-MM-DD format (default: 2006-12-31)
    --printout            Print data lines (default: False)
    --cash CASH           Cash to start with (default: 50000)
    --plot                Plot the result (default: False)
    --plot-style {bar,candle,line}
                          Plot style (default: bar)
    --no-pyfolio          Do not do pyfolio things (default: False)

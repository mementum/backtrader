from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
import sys
import argparse
import datetime

from os import listdir

import numpy as np

import backtrader as bt
from backtrader.analyzers import (AnnualReturn, DrawDown, TimeDrawDown, SharpeRatio, Returns, SQN, TimeReturn,
                                  TradeAnalyzer, annualreturn)

from analyzers import *
from strategies import *
from commissions import DegiroCommission
from strategies_plot import my_heatmap

def printResults(final_results_list):
    print('Parameter Name\t\tOldStrategy\t\tNew Strategy')
    print('--------------\t\t-----------\t\t------------')
    print('Start Worth\t\t%.2F\t\t\t%.2F'% (final_results_list[0][0][0], final_results_list[1][0][0]) )
    print('End Worth\t\t%.2F\t\t\t%.2F'% (final_results_list[0][0][1], final_results_list[1][0][1]) )
    print('PNL\t\t\t%.2F\t\t\t%.2F'% (final_results_list[0][0][2], final_results_list[1][0][2]) )
    print('Annualised returns\t%.2F\t\t\t%.2F'% (final_results_list[0][0][3], final_results_list[1][0][3]) )
    print('Annualised volatility\t%.2F\t\t\t%.2F'% (final_results_list[0][0][4], final_results_list[1][0][4]) )
    
    '''


Sharpe ratio
Sortino ratio
Beta
Maximum drawdown
Number of transactions
Mnthly average transactions
'''

def runstrategy():
    args = parse_args()

    # Get the dates from the args
    fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, args.data)

    final_results_list = []
    strategies_list = [OldStrategy, OldStrategy]
    for strat in strategies_list:
        #path = os.path.join(datapath, f'{file}')
        data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=fromdate,
            todate=todate,
            tframes=bt.TimeFrame.Minutes
        )

        cerebro = bt.Cerebro(optreturn=False)
        cerebro.adddata(data, name='MyData0')
        cerebro.addstrategy(OldStrategy, symbol='ICCM.TA', priceSize=1)

        results_list = []

        cerebro.broker.set_coc(True)
        cerebro.broker.setcash(args.cash)
        #cerebro.addsizer(MaxRiskSizer)
        comminfo = DegiroCommission()
        #cerebro.broker.addcommissioninfo(comminfo)

        tframes = dict(
            days=bt.TimeFrame.Days,
            weeks=bt.TimeFrame.Weeks,
            months=bt.TimeFrame.Months,
            years=bt.TimeFrame.Years)

        # Add the Analyzers
        cerebro.addanalyzer(SQN)
        if args.legacyannual:
            cerebro.addanalyzer(AnnualReturn, _name='time_return')
            cerebro.addanalyzer(SharpeRatio, legacyannual=True)
        else:
            cerebro.addanalyzer(TimeReturn, _name='time_return', timeframe=tframes[args.tframe])
            cerebro.addanalyzer(SharpeRatio, timeframe=tframes[args.tframe])
            cerebro.addanalyzer(Volatility)

        cerebro.addanalyzer(TradeAnalyzer)
        
        st0 = cerebro.run()

        
        
        
        my_dict = st0[0].analyzers.time_return.get_analysis()
        annual_returns = [v for _, v in my_dict.items()]
        

        startWorth = args.cash
        endWorth = round(st0[0].broker.get_value(), 2)
        PnL = round(st0[0].broker.get_value() - args.cash, 2)
        compaund_annual_return = np.power(endWorth / startWorth, 1/len(annual_returns))-1
        annualReturn = round(compaund_annual_return*100, 2)
        volatility = st0[0].analyzers.volatility.get_analysis()['volatility']

        results_list.append([
            startWorth,
            endWorth,
            PnL,
            annualReturn,
            volatility

        ])
        final_results_list.append(results_list)

    # Average results for the different data feeds
    arr = np.array(final_results_list)
    #final_results_list = [[int(val) if val.is_integer() else round(val, 2) for val in i] for i in arr.mean(0)]

    printResults(final_results_list)
    if args.plot:
        my_heatmap(final_results_list)


def parse_args():
    parser = argparse.ArgumentParser(description='TimeReturn')
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

    parser.add_argument('--data', '-d',
                        default=os.path.join(modpath,'../../datas/ICCM.TA.csv'),
                        help='data to add to the system')

    parser.add_argument('--fromdate', '-f',
                        default='2018-05-06',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2021-11-30',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--fast_period', default=13, type=int,
                        help='Period to apply to the Exponential Moving Average')

    parser.add_argument('--slow_period', default=48, type=int,
                        help='Period to apply to the Exponential Moving Average')

    parser.add_argument('--longonly', '-lo', action='store_true',
                        help='Do only long operations')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--tframe', default='years', required=False,
                       choices=['days', 'weeks', 'months', 'years'],
                       help='TimeFrame for the returns/Sharpe calculations')

    group.add_argument('--legacyannual', action='store_true',
                       help='Use legacy annual return analyzer')

    parser.add_argument('--cash', default=50000, type=int,
                        help='Starting Cash')

    parser.add_argument('--plot', '-p', action='store_true',
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1,
                        help='Plot using numfigs figures')

    parser.add_argument('--optimize', '-opt', default=1,
                        help='Plot using numfigs figures')

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
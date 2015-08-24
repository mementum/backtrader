#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import inspect
import itertools
import random
import string
import sys

import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btinds
import backtrader.observers as btobs
import backtrader.strategies as btstrats
import backtrader.analyzers as btanalyzers


DATAFORMATS = dict(
    btcsv=btfeeds.BacktraderCSVData,
    vchartcsv=btfeeds.VChartCSVData,
    vchart=btfeeds.VChartData,
    sierracsv=btfeeds.SierraChartCSVData,
    yahoocsv=btfeeds.YahooFinanceCSVData,
    yahoocsv_unreversed=btfeeds.YahooFinanceCSVData
)


def runstrat():
    args = parse_args()

    stdstats = not args.nostdstats

    cerebro = bt.Cerebro(stdstats=stdstats)

    for data in getdatas(args):
        cerebro.adddata(data)

    # Prepare a dictionary of extra args passed to push them to the strategy

    # pack them in pairs
    packedargs = itertools.izip_longest(*[iter(args.args)] * 2, fillvalue='')

    # prepare a string for evaluation, eval and store the result
    evalargs = 'dict('
    for key, value in packedargs:
        evalargs += key + '=' + value + ','
    evalargs += ')'
    stratkwargs = eval(evalargs)

    # Get the strategy and add it with any arguments
    strat = getstrategy(args)
    cerebro.addstrategy(strat, **stratkwargs)

    obs = getobservers(args)
    for ob in obs:
        cerebro.addobserver(ob)

    ans = getanalyzers(args)
    for an in ans:
        cerebro.addanalyzer(an)

    setbroker(args, cerebro)

    runsts = cerebro.run()
    runst = runsts[0]  # single strategy and no optimization

    if runst.analyzers:
        print('====================')
        print('== Analyzers')
        print('====================')
        for name, analyzer in runst.analyzers.getitems():
            print('## ', name)
            analysis = analyzer.get_analysis()
            for key, val in analysis.items():
                print('-- ', key, ':', val)

    if not args.noplot:
        cerebro.plot(numfigs=args.plotfigs, style=args.plotstyle)


def setbroker(args, cerebro):
    broker = cerebro.getbroker()

    if args.cash is not None:
        broker.setcash(args.cash)

    commkwargs = dict()
    if args.commission is not None:
        commkwargs['commission'] = args.commission
    if args.margin is not None:
        commkwargs['margin'] = args.margin
    if args.mult is not None:
        commkwargs['mult'] = args.mult

    if commkwargs:
        broker.setcommission(**commkwargs)


def getdatas(args):
    # Get the data feed class from the global dictionary
    dfcls = DATAFORMATS[args.csvformat]

    # Prepare some args
    dfkwargs = dict()
    if args.csvformat == 'yahoo_unreversed':
        dfkwargs['reverse'] = True

    fmtstr = '%Y-%m-%d'
    if args.fromdate:
        dtsplit = args.fromdate.split('T')
        if len(dtsplit) > 1:
            fmtstr += 'T%H:%M:%S'

        fromdate = datetime.datetime.strptime(args.fromdate, fmtstr)
        dfkwargs['fromdate'] = fromdate

    fmtstr = '%Y-%m-%d'
    if args.todate:
        dtsplit = args.todate.split('T')
        if len(dtsplit) > 1:
            fmtstr += 'T%H:%M:%S'
        todate = datetime.datetime.strptime(args.todate, fmtstr)
        dfkwargs['todate'] = todate

    datas = list()
    for dname in args.data:
        dfkwargs['dataname'] = dname
        data = dfcls(**dfkwargs)
        datas.append(data)

    return datas


def getmodclasses(mod, clstype, clsname=None):
    clsmembers = inspect.getmembers(mod, inspect.isclass)

    clslist = list()
    for name, cls in clsmembers:
        if not issubclass(cls, clstype):
            continue

        if clsname:
            if clsname == name:
                clslist.append(cls)
                break
        else:
            clslist.append(cls)

    return clslist


def loadmodule(modpath, modname=''):
    # generate a random name for the module
    if not modname:
        chars = string.ascii_uppercase + string.digits
        modname = ''.join(random.choice(chars) for _ in range(10))

    version = (sys.version_info[0], sys.version_info[1])

    if version < (3, 3):
        mod, e = loadmodule2(modpath, modname)
    else:
        mod, e = loadmodule3(modpath, modname)

    return mod, e


def loadmodule2(modpath, modname):
    import imp

    try:
        mod = imp.load_source(modname, modpath)
    except Exception, e:
        return (None, e)

    return (mod, None)


def loadmodule3(modpath, modname):
    import importlib.machinery

    try:
        loader = importlib.machinery.SourceFileLoader(modname, modpath)
        mod = loader.load_module()
    except Exception, e:
        return (None, e)

    return (mod, None)


def getstrategy(args):
    sttokens = args.strategy.split(':')

    if len(sttokens) == 1:
        modpath = sttokens[0]
        stname = None
    else:
        modpath, stname = sttokens

    if modpath:
        mod, e = loadmodule(modpath)

        if not mod:
            print('')
            print('Failed to load module %s:' % modpath, e)
            sys.exit(1)
    else:
        mod = btstrats

    strats = getmodclasses(mod=mod, clstype=bt.Strategy, clsname=stname)

    if not strats:
        print('No strategy %s / module %s' % (str(stname), modpath))
        sys.exit(1)

    return strats[0]


def getanalyzers(args):
    analyzers = list()
    for anspec in args.analyzers or []:

        tokens = anspec.split(':')

        if len(tokens) == 1:
            modpath = tokens[0]
            name = None
        else:
            modpath, name = tokens

        if modpath:
            mod, e = loadmodule(modpath)

            if not mod:
                print('')
                print('Failed to load module %s:' % modpath, e)
                sys.exit(1)
        else:
            mod = btanalyzers

        loaded = getmodclasses(mod=mod, clstype=bt.Analyzer, clsname=name)

        if not loaded:
            print('No analyzer %s / module %s' % ((str(name), modpath)))
            sys.exit(1)

        analyzers.extend(loaded)

    return analyzers


def getobservers(args):
    observers = list()
    for obspec in args.observers or []:

        tokens = obspec.split(':')

        if len(tokens) == 1:
            modpath = tokens[0]
            name = None
        else:
            modpath, name = tokens

        if modpath:
            mod, e = loadmodule(modpath)

            if not mod:
                print('')
                print('Failed to load module %s:' % modpath, e)
                sys.exit(1)
        else:
            mod = btobs

        loaded = getmodclasses(mod=mod, clstype=bt.Observer, clsname=name)

        if not loaded:
            print('No observer %s / module %s' % ((str(name), modpath)))
            sys.exit(1)

        observers.extend(loaded)

    return observers


def parse_args():
    parser = argparse.ArgumentParser(
        description='Backtrader Run Script')

    group = parser.add_argument_group(title='Data options')
    # Data options
    group.add_argument('--data', '-d', action='append', required=True,
                       help='Data files to be added to the system')

    datakeys = list(DATAFORMATS.keys())
    group.add_argument('--csvformat', '-c', required=False,
                       default='btcsv', choices=datakeys,
                       help='CSV Format')

    group.add_argument('--fromdate', '-f', required=False, default=None,
                       help='Starting date in YYYY-MM-DD[THH:MM:SS] format')

    group.add_argument('--todate', '-t', required=False, default=None,
                       help='Ending date in YYYY-MM-DD[THH:MM:SS] format')

    # Module where to read the strategy from
    group = parser.add_argument_group(title='Strategy options')
    group.add_argument('--strategy', '-st', required=True,
                       help=('Module and strategy to load with format '
                             'module_path:strategy_name.\n'
                             '\n'
                             'module_path:strategy_name will load '
                             'strategy_name from the given module_path\n'
                             '\n'
                             'module_path will load the module and return '
                             'the first available strategy in the module\n'
                             '\n'
                             ':strategy_name will load the given strategy '
                             'from the set of built-in strategies'))

    # Observers
    group = parser.add_argument_group(title='Observers and statistics')
    group.add_argument('--nostdstats', action='store_true',
                       help='Disable the standard statistics observers')

    group.add_argument('--observer', '-ob', dest='observers',
                       action='append', required=False,
                       help=('This option can be specified multiple times\n'
                             '\n'
                             'Module and observer to load with format '
                             'module_path:observer_name.\n'
                             '\n'
                             'module_path:observer_name will load '
                             'observer_name from the given module_path\n'
                             '\n'
                             'module_path will load the module and return '
                             'all available observers in the module\n'
                             '\n'
                             ':observer_name will load the given strategy '
                             'from the set of built-in strategies'))

    # Anaylzers
    group = parser.add_argument_group(title='Analyzers')
    group.add_argument('--analyzer', '-an', dest='analyzers',
                       action='append', required=False,
                       help=('This option can be specified multiple times\n'
                             '\n'
                             'Module and analyzer to load with format '
                             'module_path:analzyer_name.\n'
                             '\n'
                             'module_path:analyzer_name will load '
                             'observer_name from the given module_path\n'
                             '\n'
                             'module_path will load the module and return '
                             'all available analyzers in the module\n'
                             '\n'
                             ':anaylzer_name will load the given strategy '
                             'from the set of built-in strategies'))

    # Broker/Commissions
    group = parser.add_argument_group(title='Cash and Commission Scheme Args')
    group.add_argument('--cash', '-cash', required=False, type=float,
                       help='Cash to set to the broker')
    group.add_argument('--commission', '-comm', required=False, type=float,
                       help='Commission value to set')
    group.add_argument('--margin', '-marg', required=False, type=float,
                       help='Margin type to set')

    group.add_argument('--mult', '-mul', required=False, type=float,
                       help='Multiplier to use')

    # Plot options
    group = parser.add_argument_group(title='Plotting options')
    group.add_argument('--noplot', '-np', action='store_true', required=False,
                       help='Do not plot the read data')

    group.add_argument('--plotstyle', '-ps', required=False, default='bar',
                       choices=['bar', 'line', 'candle'],
                       help='Plot style for the input data')

    group.add_argument('--plotfigs', '-pn', required=False, default=1,
                       type=int, help='Plot using n figures')

    # Extra arguments
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='args to pass to the loaded strategy')

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()

#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
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

from backtrader.utils.py3 import range

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


def btrun(pargs=''):
    args = parse_args(pargs)

    stdstats = not args.nostdstats

    cer_kwargs_str = args.cerebro
    cer_kwargs = eval('dict(' + cer_kwargs_str + ')')
    if 'stdstats' not in cer_kwargs:
        cer_kwargs.update(stdstats=stdstats)

    cerebro = bt.Cerebro(**cer_kwargs)

    for data in getdatas(args):
        cerebro.adddata(data)

    # get and add strategies
    strategies = getobjects(args.strategies, bt.Strategy, bt.strategies)
    if not strategies:
        # Add the base Strategy with no args if nothing specified
        strategies.append((bt.Strategy, dict()))

    for strat, kwargs in strategies:
        cerebro.addstrategy(strat, **kwargs)

    inds = getobjects(args.indicators, bt.Indicator, bt.indicators)
    for ind, kwargs in inds:
        cerebro.addindicator(ind, **kwargs)

    obs = getobjects(args.observers, bt.Observer, bt.observers)
    for ob, kwargs in obs:
        cerebro.addobserver(ob, **kwargs)

    ans = getobjects(args.analyzers, bt.Analyzer, bt.analyzers)
    for an, kwargs in ans:
        cerebro.addanalyzer(an, **kwargs)

    setbroker(args, cerebro)

    for wrkwargs_str in args.writers or []:
        wrkwargs = eval('dict(' + wrkwargs_str + ')')
        cerebro.addwriter(bt.WriterFile, **wrkwargs)

    runsts = cerebro.run()
    runst = runsts[0]  # single strategy and no optimization

    if args.pranalyzer or args.ppranalyzer:
        if runst.analyzers:
            print('====================')
            print('== Analyzers')
            print('====================')
            for name, analyzer in runst.analyzers.getitems():
                if args.pranalyzer:
                    analyzer.print()
                elif args.ppranalyzer:
                    print('##########')
                    print(name)
                    print('##########')
                    analyzer.pprint()

    if args.plot:
        if args.plot is not True:
            # evaluates to True but is not "True" - args were passed
            pkwargs = eval('dict(' + args.plot + ')')
        else:
            pkwargs = dict()

        # cerebro.plot(numfigs=args.plotfigs, style=args.plotstyle)
        cerebro.plot(**pkwargs)


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

    if not modpath.endswith('.py'):
        modpath += '.py'

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
    except Exception as e:
        return (None, e)

    return (mod, None)


def loadmodule3(modpath, modname):
    import importlib.machinery

    try:
        loader = importlib.machinery.SourceFileLoader(modname, modpath)
        mod = loader.load_module()
    except Exception as e:
        return (None, e)

    return (mod, None)


def getobjects(iterable, clsbase, modbase):
    retobjects = list()

    for item in iterable or []:
        tokens = item.split(':', 1)

        if len(tokens) == 1:
            modpath = tokens[0]
            name = ''
            kwargs = dict()
        else:
            modpath, name = tokens
            kwtokens = name.split(':', 1)
            if len(kwtokens) == 1:
                # no '(' found
                kwargs = dict()
            else:
                name = kwtokens[0]
                kwtext = 'dict(' + kwtokens[1] + ')'
                kwargs = eval(kwtext)

        if modpath:
            mod, e = loadmodule(modpath)

            if not mod:
                print('')
                print('Failed to load module %s:' % modpath, e)
                sys.exit(1)
        else:
            mod = modbase

        loaded = getmodclasses(mod=mod, clstype=clsbase, clsname=name)

        if not loaded:
            print('No class %s / module %s' % (str(name), modpath))
            sys.exit(1)

        retobjects.append((loaded[0], kwargs))

    return retobjects


def parse_args(pargs=''):
    parser = argparse.ArgumentParser(
        description='Backtrader Run Script',
        formatter_class=argparse.RawTextHelpFormatter,
    )

    group = parser.add_argument_group(title='Data options')
    # Data options
    group.add_argument('--data', '-d', action='append', required=True,
                       help='Data files to be added to the system')

    group = parser.add_argument_group(title='Cerebro options')
    group.add_argument(
        '--cerebro', '-cer',
        metavar='kwargs',
        required=False, const='', default='', nargs='?',
        help=('The argument can be specified with the following form:\n'
              '\n'
              '  - kwargs\n'
              '\n'
              '    Example: "preload=True" which set its to True\n'
              '\n'
              'The passed kwargs will be passed directly to the cerebro\n'
              'instance created for the execution\n'
              '\n'
              'The available kwargs to cerebro are:\n'
              '  - preload (default: True)\n'
              '  - runonce (default: True)\n'
              '  - maxcpus (default: None)\n'
              '  - stdstats (default: True)\n'
              '  - exactbars (default: )\n'
              '  - preload (default: True)\n'
              '  - writer (default False)\n')
    )

    group.add_argument('--nostdstats', action='store_true',
                       help='Disable the standard statistics observers')

    datakeys = list(DATAFORMATS)
    group.add_argument('--csvformat', '-c', required=False,
                       default='btcsv', choices=datakeys,
                       help='CSV Format')

    group.add_argument('--fromdate', '-f', required=False, default=None,
                       help='Starting date in YYYY-MM-DD[THH:MM:SS] format')

    group.add_argument('--todate', '-t', required=False, default=None,
                       help='Ending date in YYYY-MM-DD[THH:MM:SS] format')

    # Module where to read the strategy from
    group = parser.add_argument_group(title='Strategy options')
    group.add_argument(
        '--strategy', '-st', dest='strategies',
        action='append', required=False,
        metavar='module:name:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in strategies module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st strategy found in the\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )

    # Observers
    group = parser.add_argument_group(title='Observers and statistics')
    group.add_argument(
        '--observer', '-ob', dest='observers',
        action='append', required=False,
        metavar='module:name:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in observers module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st observer found in the\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )
    # Analyzers
    group = parser.add_argument_group(title='Analyzers')
    group.add_argument(
        '--analyzer', '-an', dest='analyzers',
        action='append', required=False,
        metavar='module:name:kwargs',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in analyzers module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st analyzer found in the\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )

    # Analyzer - Print
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--pranalyzer', '-pralyzer',
                       required=False, action='store_true',
                       help=('Automatically print analyzers'))

    group.add_argument('--ppranalyzer', '-ppralyzer',
                       required=False, action='store_true',
                       help=('Automatically PRETTY print analyzers'))

    # Indicators
    group = parser.add_argument_group(title='Indicators')
    group.add_argument(
        '--indicator', '-ind', dest='indicators',
        metavar='module:name:kwargs',
        action='append', required=False,
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - module:classname:kwargs\n'
              '\n'
              '    Example: mymod:myclass:a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'If module is omitted then class name will be sought in\n'
              'the built-in analyzers module. Such as in:\n'
              '\n'
              '  - :name:kwargs or :name\n'
              '\n'
              'If name is omitted, then the 1st analyzer found in the\n'
              'will be used. Such as in:\n'
              '\n'
              '  - module or module::kwargs')
    )

    # Writer
    group = parser.add_argument_group(title='Writers')
    group.add_argument(
        '--writer', '-wr',
        dest='writers', metavar='kwargs', nargs='?',
        action='append', required=False, const='',
        help=('This option can be specified multiple times.\n'
              '\n'
              'The argument can be specified with the following form:\n'
              '\n'
              '  - kwargs\n'
              '\n'
              '    Example: a=1,b=2\n'
              '\n'
              'kwargs is optional\n'
              '\n'
              'It creates a system wide writer which outputs run data\n'
              '\n'
              'Please see the documentation for the available kwargs')
    )

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
    parser.add_argument(
        '--plot', '-p', nargs='?',
        metavar='kwargs',
        default=False, const=True, required=False,
        help=('Plot the read data applying any kwargs passed\n'
              '\n'
              'For example:\n'
              '\n'
              '  --plot style="candle" (to plot candlesticks)\n')
    )

    if pargs:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    btrun()

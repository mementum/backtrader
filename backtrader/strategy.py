#!/usr/bin389/env python
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

import collections
import itertools
import operator

from .utils.py3 import (filter, map, with_metaclass, string_types, keys,
                        iteritems)

from .broker import BrokerBack
from .lineiterator import LineIterator, StrategyBase
from .metabase import ItemCollection
from .sizer import SizerFix
from .trade import Trade
from .utils import OrderedDict, AutoOrderedDict, AutoDictList


class MetaStrategy(StrategyBase.__class__):
    _indcol = dict()

    def __new__(meta, name, bases, dct):
        # Hack to support original method name for notify_order
        if 'notify' in dct:
            # rename 'notify' to 'notify_order'
            dct['notify_order'] = dct.pop('notify')
        if 'notify_operation' in dct:
            # rename 'notify' to 'notify_order'
            dct['notify_trade'] = dct.pop('notify_operation')

        return super(MetaStrategy, meta).__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        '''
        Class has already been created ... register subclasses
        '''
        # Initialize the class
        super(MetaStrategy, cls).__init__(name, bases, dct)

        if not cls.aliased and \
           name != 'Strategy' and not name.startswith('_'):
            cls._indcol[name] = cls

    def dopreinit(cls, _obj, env, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj.env = env
        _obj.broker = env.broker
        _obj._sizer = SizerFix()
        _obj._orders = list()
        _obj._orderspending = list()
        _obj._trades = collections.defaultdict(AutoDictList)
        _obj._tradespending = list()

        _obj.stats = _obj.observers = ItemCollection()
        _obj.analyzers = ItemCollection()
        _obj.writers = list()

        _obj._tradehistoryon = False

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopostinit(_obj, *args, **kwargs)

        if not _obj._sizer.getbroker():
            _obj._sizer.setbroker(_obj.broker)

        return _obj, args, kwargs


class Strategy(with_metaclass(MetaStrategy, StrategyBase)):
    '''
    Base class to be subclassed for user defined strategies.
    '''

    _ltype = LineIterator.StratType

    csv = True

    # This unnamed line is meant to allow having "len" and "forwarding"
    extralines = 1

    def ringbuffer(self, maxlen=-1):
        super(Strategy, self).ringbuffer(maxlen=maxlen)

        # Activate it for all sub lineiterators
        for objtype in self._lineiterators:
            for obj in self._lineiterators[objtype]:
                obj.ringbuffer(maxlen=maxlen)

        # Activate it for the datas with the calculated minperiods
        # because datas have not recalculated own periods
        for i, period in enumerate(self._minperiods):
            self.datas[i].ringbuffer(maxlen=period)

    def _periodset(self):
        dataids = [id(data) for data in self.datas]

        _dminperiods = collections.defaultdict(list)
        for lineiter in self._lineiterators[LineIterator.IndType]:
            # if multiple datas are used and multiple timeframes the larger
            # timeframe may place larger time constraints in calling next.
            clk = getattr(lineiter, '_clock', None)
            if clk is None:
                clk = getattr(lineiter._owner, '_clock', None)
                if clk is None:
                    continue

            while True:
                if id(clk) in dataids:
                    break

                clk2 = getattr(clk, '._clock', None)
                if clk2 is None:
                    clk2 = getattr(clk._owner, '._clock', None)

                clk = clk2
                if clk is None:
                    break

            if clk is None:
                continue

            _dminperiods[clk].append(lineiter._minperiod)

        self._minperiods = list()
        for data in self.datas:
            # dminperiod = max(_dminperiods[data] or [self._minperiod])
            dminperiod = max(_dminperiods[data] or [data._minperiod])
            self._minperiods.append(dminperiod)

        # Set the minperiod
        minperiods = \
            [x._minperiod for x in self._lineiterators[LineIterator.IndType]]
        self._minperiod = max(minperiods or [self._minperiod])

    def _addwriter(self, writer):
        '''
        Unlike the other _addxxx functions this one receives an instance
        because the writer works at cerebro level and is only passed to the
        strategy to simplify the logic
        '''
        self.writers.append(writer)

    def _addindicator(self, indcls, *indargs, **indkwargs):
        indcls(*indargs, **indkwargs)

    def _addanalyzer(self, ancls, *anargs, **ankwargs):
        anname = ankwargs.pop('_name', '') or ancls.__name__.lower()
        analyzer = ancls(*anargs, **ankwargs)
        self.analyzers.append(analyzer, anname)

    def _addobserver(self, multi, obscls, *obsargs, **obskwargs):
        obsname = obskwargs.pop('obsname', '')
        if not obsname:
            obsname = obscls.__name__.lower()

        if not multi:
            newargs = list(itertools.chain(self.datas, obsargs))
            obs = obscls(*newargs, **obskwargs)
            self.stats.append(obs, obsname)
            return

        setattr(self.stats, obsname, list())
        l = getattr(self.stats, obsname)

        for data in self.datas:
            obs = obscls(data, *obsargs, **obskwargs)
            l.append(obs)

    def _getminperstatus(self):
        # check the min period status connected to datas
        dlens = map(operator.sub, self._minperiods, map(len, self.datas))
        minperstatus = max(dlens)
        return minperstatus

    def _oncepost(self):
        for indicator in self._lineiterators[LineIterator.IndType]:
            indicator.advance()

        self.advance()
        self._notify()

        minperstatus = self._getminperstatus()

        if minperstatus < 0:
            self.next()
        elif minperstatus == 0:
            self.nextstart()  # only called for the 1st value
        else:
            self.prenext()

        self._next_observers(minperstatus, once=True)
        self._next_analyzers(minperstatus, once=True)

        self.clear()

    def _next(self):
        super(Strategy, self)._next()

        minperstatus = self._getminperstatus()
        self._next_observers(minperstatus)
        self._next_analyzers(minperstatus)

        self.clear()

    def _next_observers(self, minperstatus, once=False):
        for observer in self._lineiterators[LineIterator.ObsType]:
            if once:
                observer.advance()
                if minperstatus < 0:
                    observer.next()
                elif minperstatus == 0:
                    observer.nextstart()  # only called for the 1st value
                else:
                    observer.prenext()
            else:
                observer._next()

    def _next_analyzers(self, minperstatus, once=False):
        for analyzer in self.analyzers:
            if minperstatus < 0:
                analyzer._next()
            elif minperstatus == 0:
                analyzer._nextstart()  # only called for the 1st value
            else:
                analyzer._prenext()

    def _start(self):
        self._periodset()

        # change operators to stage 2
        self._stage2()

        for analyzer in self.analyzers:
            analyzer._start()

        self.start()

    def start(self):
        '''
        Called right before the backtesting is about to be started
        '''
        pass

    def getwriterheaders(self):
        self.indobscsv = [self]

        indobs = itertools.chain(self.getindicators(), self.getobservers())
        self.indobscsv.extend(filter(lambda x: x.csv, indobs))

        headers = list()

        # prepare the indicators/observers data headers
        for iocsv in self.indobscsv:
            headers.append(iocsv.__class__.__name__)
            headers.append('len')
            headers.extend(iocsv.getlinealiases())

        return headers

    def getwritervalues(self):
        values = list()

        for iocsv in self.indobscsv:
            values.append(iocsv.__class__.__name__)
            values.append(len(iocsv))
            values.extend(map(lambda l: l[0], iocsv.lines.itersize()))

        return values

    def getwriterinfo(self):
        wrinfo = AutoOrderedDict()

        wrinfo['Params'] = self.p._getkwargs()

        sections = [
            ['Indicators', self.getindicators()],
            ['Observers', self.getobservers()]
        ]

        for sectname, sectitems in sections:
            sinfo = wrinfo[sectname]
            for item in sectitems:
                itname = item.__class__.__name__
                sinfo[itname].Lines = item.lines.getlinealiases() or None
                sinfo[itname].Params = item.p._getkwargs() or None

        ainfo = wrinfo.Analyzers

        # Internal Value Analyzer
        ainfo.Value.Begin = self.broker.startingcash
        ainfo.Value.End = self.broker.getvalue()

        for analyzer in self.analyzers:
            aname = analyzer.__class__.__name__
            ainfo[aname].Params = item.p._getkwargs() or None
            ainfo[aname].Analysis = analyzer.get_analysis()

        return wrinfo

    def _stop(self):
        self.stop()

        for analyzer in self.analyzers:
            analyzer._stop()

        # change operators back to stage 1 - allows reuse of datas
        self._stage1()

    def stop(self):
        '''
        Called right before the backtesting is about to be stopped
        '''
        pass

    def set_tradehistory(self, onoff=True):
        self._tradehistoryon = onoff

    def clear(self):
        self._orders.extend(self._orderspending)
        self._orderspending = list()
        self._tradespending = list()

    def _addnotification(self, order):
        self._orderspending.append(order)

        if not order.executed.size:
            return

        tradedata = order.data
        datatrades = self._trades[tradedata][order.tradeid]
        if not datatrades:
            trade = Trade(data=tradedata, tradeid=order.tradeid,
                          historyon=self._tradehistoryon)
            datatrades.append(trade)
        else:
            trade = datatrades[-1]

        for exbit in order.executed.exbits:
            if exbit.closed:
                trade.update(order,
                             exbit.closed,
                             exbit.price,
                             exbit.closedvalue,
                             exbit.closedcomm,
                             exbit.pnl,
                             comminfo=order.comminfo)

                if trade.isclosed:
                    self._tradespending.append(trade)

            # Update it if needed
            if exbit.opened:
                if trade.isclosed:
                    trade = Trade(data=tradedata, tradeid=order.tradeid,
                                  historyon=self._tradehistoryon)
                    datatrades.append(trade)

                trade.update(order,
                             exbit.opened,
                             exbit.price,
                             exbit.openedvalue,
                             exbit.openedcomm,
                             exbit.pnl,
                             comminfo=order.comminfo)

                # This extra check covers the case in which different tradeid
                # orders have put the position down to 0 and the next order
                # "opens" a position but "closes" the trade
                if trade.isclosed:
                    self._tradespending.append(trade)

            if trade.justopened:
                self._tradespending.append(trade)

    def _notify(self):
        for order in self._orderspending:
            self.notify_order(order)
            for analyzer in self.analyzers:
                analyzer._notify_order(order)

        for trade in self._tradespending:
            self.notify_trade(trade)
            for analyzer in self.analyzers:
                analyzer._notify_trade(trade)

        cash = self.broker.getcash()
        value = self.broker.getvalue()

        self.notify_cashvalue(cash, value)
        for analyzer in self.analyzers:
            analyzer._notify_cashvalue(cash, value)

    def notify_cashvalue(self, cash, value):
        '''
        Receives the current cash, value status of the strategy's broker
        '''
        pass

    def notify_order(self, order):
        '''
        Receives an order whenever there has been a change in one
        '''
        pass

    def notify_trade(self, trade):
        '''
        Receives a trade whenever there has been a change in one
        '''
        pass

    def getdatanames(self):
        '''
        Returns a list of the existing data names
        '''
        return keys(self.env.datasbyname)

    def getdatabyname(self, name):
        '''
        Returns a given data by name using the environment (cerebro)
        '''
        return self.env.datasbyname[name]

    def buy(self, data=None,
            size=None, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, **kwargs):
        '''
        To create a buy (long) order and send it to the broker

        Returns: the submitted order
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data or self.datas[0]
        size = size or self.getsizing(data)

        return self.broker.buy(
            self, data,
            size=size, price=price, plimit=plimit,
            exectype=exectype, valid=valid, tradeid=tradeid, **kwargs)

    def sell(self, data=None,
             size=None, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, **kwargs):
        '''
        To create a selll (short) order and send it to the broker

        Returns: the submitted order
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data or self.datas[0]
        size = size or self.getsizing(data)

        return self.broker.sell(
            self, data,
            size=size, price=price, plimit=plimit,
            exectype=exectype, valid=valid, tradeid=tradeid, **kwargs)

    def close(self,
              data=None, size=None, price=None, exectype=None, valid=None,
              tradeid=0, **kwargs):
        '''
        Counters a long/short position closing it

        Returns: the submitted order
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        possize = self.getposition(data, self.broker).size
        size = abs(size or possize)

        if possize > 0:
            return self.sell(data, size, price, exectype, valid,
                             tradeid=tradeid, **kwargs)
        elif possize < 0:
            return self.buy(data, size, price, exectype, valid,
                            tradeid=tradeid, **kwargs)

        return None

    def getposition(self, data=None, broker=None):
        '''
        Returns the current position for a given data in a given broker.

        If both are None, the main data and the default broker will be used

        A property ``position`` is also available
        '''
        data = data or self.datas[0]
        broker = broker or self.broker
        return broker.getposition(data)

    position = property(getposition)

    def getpositionbyname(self, name=None, broker=None):
        '''
        Returns the current position for a given name in a given broker.

        If both are None, the main data and the default broker will be used

        A property ``positionbyname`` is also available
        '''
        data = self.datas[0] if not name else self.getdatabyname(name)
        broker = broker or self.broker
        return broker.getposition(data)

    positionbyname = property(getpositionbyname)

    def getpositions(self, broker=None):
        '''
        Returns the current by data positions directly from the broker

        If the given ``broker`` is None, the default broker will be used

        A property ``positions`` is also available
        '''
        broker = broker or self.broker
        return broker.positions

    positions = property(getpositions)

    def getpositionsbyname(self, broker=None):
        '''
        Returns the current by name positions directly from the broker

        If the given ``broker`` is None, the default broker will be used

        A property ``positionsbyname`` is also available
        '''
        broker = broker or self.broker
        positions = broker.positions

        posbyname = collections.OrderedDict()
        for name, data in iteritems(self.env.datasbyname):
            posbyname[name] = positions[data]

        return posbyname

    positionsbyname = property(getpositionsbyname)

    def setsizer(self, sizer):
        '''
        Replace the default (fixed stake) sizer
        '''
        self._sizer = sizer
        if not sizer.getbroker():
            sizer.setbroker(self.broker)
        return sizer

    def getsizer(self):
        '''
        Returns the sizer which is in used if automatic statke calculation is
        used

        Also available as ``sizer``
        '''
        return self._sizer

    sizer = property(getsizer, setsizer)

    def getsizing(self, data=None):
        '''
        Return the stake calculated by the sizer instance for the current
        situation
        '''
        data = data or self.datas[0]
        return self._sizer.getsizing(data)

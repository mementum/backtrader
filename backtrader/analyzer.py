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

import pprint as pp

import backtrader as bt
from backtrader.utils.py3 import with_metaclass


class MetaAnalyzer(bt.MetaParams):
    def donew(cls, *args, **kwargs):
        '''
        Intercept the strategy parameter
        '''
        # Create the object and set the params in place
        _obj, args, kwargs = super(MetaAnalyzer, cls).donew(*args, **kwargs)

        _obj._children = list()

        _obj.strategy = strategy = bt.metabase.findowner(_obj, bt.Strategy)
        _obj._parent = bt.metabase.findowner(_obj, Analyzer)

        _obj.datas = strategy.datas

        # For each data add aliases: for first data: data and data0
        if _obj.datas:
            _obj.data = data = _obj.datas[0]

            for l, line in enumerate(data.lines):
                linealias = data._getlinealias(l)
                if linealias:
                    setattr(_obj, 'data_%s' % linealias, line)
                setattr(_obj, 'data_%d' % l, line)

            for d, data in enumerate(_obj.datas):
                setattr(_obj, 'data%d' % d, data)

                for l, line in enumerate(data.lines):
                    linealias = data._getlinealias(l)
                    if linealias:
                        setattr(_obj, 'data%d_%s' % (d, linealias), line)
                    setattr(_obj, 'data%d_%d' % (d, l), line)

        # Return to the normal chain
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaAnalyzer, cls).dopostinit(_obj, *args, **kwargs)

        if _obj._parent is not None:
            _obj._parent._register(_obj)

        # Return to the normal chain
        return _obj, args, kwargs


class Analyzer(with_metaclass(MetaAnalyzer, object)):
    '''Analyzer base class. All analyzers are subclass of this one

    An Analyzer instance operates in the frame of a strategy and provides an
    analysis for that strategy.

    Automagically set member attributes:

      - self.strategy (giving access to the strategy and anything accessible
        from it)

      - self.datas[x] giving access to the array of datas present in the the
        system, which could also be accessed via the strategy reference

      - self.data, giving access to self.datas[0]

      - self.dataX -> self.datas[X]

      - self.dataX_Y -> self.datas[X].lines[Y]

      - self.dataX_name -> self.datas[X].name

      - self.data_name -> self.datas[0].name

      - self.data_Y -> self.datas[0].lines[Y]

    This is not a *Lines* object, but the methods and operation follow the same
    design

      - __init__ during instantiation and initial setup

      - ``start`` / ``stop`` to signal the begin and end of operations

      - ``prenext`` / ``nextstart`` / ``next`` family of methods that follow
        the calls made to the same methods in the strategy

      - ``notify_trade`` / ``notify_order`` / ``notify_cashvalue`` which
        receive the same notifications as the equivalent methods of the
        strategy

    The mode of operation is open and no pattern is preferred. As such the
    analysis can be generated with the ``next`` calls, at the end of operations
    during ``stop`` and even with a single method like ``notify_trade``

    The important thing is to override ``get_analysis`` to return a  dict-like
    object containing the results of the analysis (the actual format is
    implementation dependent)
    '''
    csv = True

    def __len__(self):
        '''Support for invoking ``len`` on analyzers by actually returning the
        current length of the strategy the analyzer operates on'''
        return len(self.strategy)

    def _register(self, child):
        self._children.append(child)

    def _prenext(self):
        for child in self._children:
            child._prenext()

        self.prenext()

    def _notify_cashvalue(self, cash, value):
        for child in self._children:
            child._notify_cashvalue(cash, value)

        self.notify_cashvalue(cash, value)

    def _notify_trade(self, trade):
        for child in self._children:
            child._notify_trade(trade)

        self.notify_trade(trade)

    def _notify_order(self, order):
        for child in self._children:
            child._notify_order(order)

        self.notify_order(order)

    def _nextstart(self):
        for child in self._children:
            child._nextstart()

        self.nextstart()

    def _next(self):
        for child in self._children:
            child._next()

        self.next()

    def _start(self):
        for child in self._children:
            child._start()

        self.start()

    def _stop(self):
        for child in self._children:
            child._stop()

        self.stop()

    def notify_cashvalue(self, cash, value):
        '''Receives the cash/value notification before each next cycle'''
        pass

    def notify_order(self, order):
        '''Receives order notifications before each next cycle'''
        pass

    def notify_trade(self, trade):
        '''Receives trade notifications before each next cycle'''
        pass

    def next(self):
        '''Invoked for each next invocation of the strategy, once the minum
        preiod of the strategy has been reached'''
        pass

    def prenext(self):
        '''Invoked for each prenext invocation of the strategy, until the minimum
        preiod of the strategy has been reached
        '''
        pass

    def nextstart(self):
        '''Invoked exactly once for the nextstart invocation of the strategy,
        when the minimum period has been first reached
        '''
        self.next()

    def start(self):
        '''Invoked to indicate the start of operations, giving the analyzer
        time to setup up needed things'''
        pass

    def stop(self):
        '''Invoked to indicate the end of operations, giving the analyzer
        time to shut down needed things'''
        pass

    def get_analysis(self):
        '''Returns a dict-like object with the results of the analysis

        The keys and format of analysis results in the dictionary is
        implementation dependent.

        It is not even enforced that the result is a dict-like object, just the
        convention
        '''
        return dict()

    def print(self, *args, **kwargs):
        '''Prints the results returned by ``get_analysis`` via a standard
        ``Writerfile`` object, which defaults to writing things to standard
        output
        '''
        writer = bt.WriterFile(*args, **kwargs)
        writer.start()
        pdct = dict()
        pdct[self.__class__.__name__] = self.get_analysis()
        writer.writedict(pdct)
        writer.stop()

    def pprint(self, *args, **kwargs):
        '''Prints the results returned by ``get_analysis`` using the pretty
        print Python module (*pprint*)
        '''
        pp.pprint(self.get_analysis(), *args, **kwargs)

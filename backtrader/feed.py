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

import collections
import datetime
import inspect
import os.path

from backtrader import date2num, time2num, TimeFrame, dataseries, metabase
from backtrader.utils.py3 import with_metaclass, bytes, map, zip


class MetaAbstractDataBase(dataseries.OHLCDateTime.__class__):
    _indcol = dict()

    def __init__(cls, name, bases, dct):
        '''
        Class has already been created ... register subclasses
        '''
        # Initialize the class
        super(MetaAbstractDataBase, cls).__init__(name, bases, dct)

        if not cls.aliased and \
           name != 'DataBase' and not name.startswith('_'):
            cls._indcol[name] = cls

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaAbstractDataBase, cls).dopreinit(_obj, *args, **kwargs)

        # Find the owner and store it
        _obj._feed = metabase.findowner(_obj, FeedBase)

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaAbstractDataBase, cls).dopostinit(_obj, *args, **kwargs)

        _obj._name = _obj.p.name
        _obj._compression = _obj.p.compression
        _obj._timeframe = _obj.p.timeframe

        if isinstance(_obj.p.sessionstart, datetime.datetime):
            _obj.p.sessionstart = _obj.p.sessionstart.time()

        if _obj.p.sessionstart is None:
            _obj.p.sessionstart = datetime.time(0, 0, 0)

        if isinstance(_obj.p.sessionend, datetime.datetime):
            _obj.p.sessionend = _obj.p.sessionend.time()

        if _obj.p.sessionend is None:
            _obj.p.sessionend = datetime.time(23, 59, 59)

        if isinstance(_obj.p.fromdate, datetime.date):
            # push it to the end of the day, or else intraday
            # values before the end of the day would be gone
            _obj.p.fromdate = datetime.datetime.combine(
                _obj.p.fromdate, _obj.p.sessionstart)

        if isinstance(_obj.p.todate, datetime.date):
            # push it to the end of the day, or else intraday
            # values before the end of the day would be gone
            _obj.p.todate = datetime.datetime.combine(
                _obj.p.todate, _obj.p.sessionend)

        _obj.fromdate = date2num(_obj.p.fromdate)
        _obj.todate = date2num(_obj.p.todate)
        _obj.sessionstart = time2num(_obj.p.sessionstart)
        _obj.sessionend = time2num(_obj.p.sessionend)

        # hold datamaster points corresponding to own
        _obj.mlen = list()

        _obj.funcfilters = list()
        for ff in _obj.p.funcfilters:
            if inspect.isclass(ff):
                ff = ff(_obj)

            _obj.funcfilters.append([ff])

        _obj.funcprocessors = list()
        for fp in _obj.p.funcprocessors:
            # print('Got fp', fp)
            if inspect.isclass(fp):
                fp = fp(_obj)

            _obj.funcprocessors.append([fp])

        return _obj, args, kwargs


class AbstractDataBase(with_metaclass(MetaAbstractDataBase,
                                      dataseries.OHLCDateTime)):
    params = (('dataname', None),
              ('fromdate', datetime.datetime.min),
              ('todate', datetime.datetime.max),
              ('name', ''),
              ('compression', 1),
              ('timeframe', TimeFrame.Days),
              ('sessionstart', None),
              ('sessionend', None),
              ('funcfilters', []),
              ('funcprocessors', []))

    _feed = None

    def getfeed(self):
        return self._feed

    def start(self):
        self._barstack = collections.deque()

    def stop(self):
        pass

    def addfilter(self, f, *args, **kwargs):
        if inspect.isclass(f):
            fobj = f(self, *args, **kwargs)
            self.funcfilters.append((fobj, [], {}))
        else:
            self.funcfilters.append((f, args, kwargs))

    def addprocessor(self, p, *args, **kwargs):
        if inspect.isclass(p):
            pobj = p(self, *args, **kwargs)
            self.funcprocessors.append((pobj, [], {}))
        else:
            self.funcprocessors.append((p, args, kwargs))

    def _tick_nullify(self):
        # These are the updating prices in case the new bar is "updated"
        # and the length doesn't change like if a replay is happening or
        # a real-time data feed is in use and 1 minutes bars are being
        # constructed with 5 seconds updates
        self.tick_open = None
        self.tick_high = None
        self.tick_low = None
        self.tick_close = self.tick_last = None
        self.tick_volume = None
        self.tick_openinterest = None

    def _tick_fill(self):
        # If nothing filled the tick_xxx attributes, the bar is the tick
        if self.tick_open is None:
            self.tick_open = self.lines.open[0]
            self.tick_high = self.lines.high[0]
            self.tick_low = self.lines.low[0]
            self.tick_close = self.tick_last = self.lines.close[0]
            self.tick_volume = self.lines.volume[0]
            self.tick_openinterest = self.lines.openinterest[0]

    def advance(self, size=1, datamaster=None):
        self._tick_nullify()

        # Need intercepting this call to support datas with
        # different lengths (timeframes)
        self.lines.advance(size)

        if datamaster:
            if len(self) > self.buflen():
                # if no bar can be delivered, fill with an empty bar
                self.rewind()
                self.lines.forward()
                return

            if self.lines.datetime[0] > datamaster.lines.datetime[0]:
                self.lines.rewind()
            else:
                self.mlen.append(len(datamaster))
                self._tick_fill()
        elif len(self) < self.buflen():
            # a resampler may have advance us past the last point
            self._tick_fill()

    def next(self, datamaster=None):

        if len(self) >= self.buflen():
            self._tick_nullify()

            # not preloaded - request next bar
            ret = self.load()
            if not ret:
                # if load cannot produce more bars - forward the result
                return ret

            if not datamaster:
                # bar is there and no master ... return load's result
                return ret

        else:
            self.advance()

        # a bar is "loaded" or was preloaded - index has been moved to it
        if datamaster:
            # there is a time reference to check against
            if self.lines.datetime[0] > datamaster.lines.datetime[0]:
                # can't deliver new bar, too early, go back
                self.rewind()
            else:
                self.mlen.append(len(datamaster))
                self._tick_fill()

        else:
            self._tick_fill()

        # tell the world there is a bar (either the new or the previous
        return True

    def preload(self):
        while self.load():
            pass

        self.home()

    def load(self):
        while True:
            # move data pointer forward for new bar
            self.forward()

            if self._fromstack():
                return True

            if not self._load():
                # no bar - undo data pointer
                self.backwards()
                break

            dt = self.lines.datetime[0]
            if dt < self.fromdate:
                # discard loaded bar and carry on
                self.backwards()
                continue
            if dt > self.todate:
                # discard loaded bar and break out
                self.backwards()
                break

            # Check filters passed to the data
            if any(map(lambda x: not x[0](self, *x[1], **x[2]), self.funcfilters)):
                # if any filter returns False ... discard bar
                self.backwards()
                continue

            # Pass through processors - if any returns True ... loop again
            if any(map(lambda x: x[0](self, *x[1], **x[2]), self.funcprocessors)):
                self._save2stack()
                self.backwards()
                continue

            # Checks let the bar through ... notify it
            return True

        # Out of the loop ... no more bars or past todate
        return False

    def _load(self):
        return False

    def _add2stack(self, bar):
        '''Saves current bar to the bar stack for later retrieval'''
        self._barstack.append(bar)

    def _save2stack(self):
        '''Saves current bar to the bar stack for later retrieval'''
        bar = [line[0] for line in self.itersize()]
        self._barstack.append(bar)

    def _fromstack(self):
        '''Load a value from the stack onto the lines to form the new bar

        Returns True if values are present, False otherwise
        '''
        if self._barstack:
            for line, val in zip(self.itersize(), self._barstack.popleft()):
                line[0] = val

            return True

        return False


class DataBase(AbstractDataBase):
    pass


class FeedBase(with_metaclass(metabase.MetaParams, object)):
    params = () + DataBase.params._gettuple()

    def __init__(self):
        self.datas = list()

    def start(self):
        for data in self.datas:
            data.start()

    def stop(self):
        for data in self.datas:
            data.stop()

    def getdata(self, dataname, name=None, **kwargs):
        for pname, pvalue in self.p._getitems():
            kwargs.setdefault(pname, getattr(self.p, pname))

        kwargs['dataname'] = dataname
        data = self._getdata(**kwargs)

        data._name = name

        self.datas.append(data)
        return data

    def _getdata(self, dataname, **kwargs):
        for pname, pvalue in self.p._getitems():
            kwargs.setdefault(pname, getattr(self.p, pname))

        kwargs['dataname'] = dataname
        return self.DataCls(**kwargs)


class MetaCSVDataBase(DataBase.__class__):
    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaCSVDataBase, cls).dopostinit(_obj, *args, **kwargs)

        if not _obj._name:
            _obj._name, _ = os.path.splitext(os.path.basename(_obj.p.dataname))

        return _obj, args, kwargs


class CSVDataBase(with_metaclass(MetaCSVDataBase, DataBase)):
    '''
    Base class for classes implementing CSV DataFeeds

    The class takes care of opening the file, reading the lines and
    tokenizing them.

    Subclasses do only need to override:

      - _loadline(tokens)

    The return value of ``_loadline`` (True/False) will be the return value
    of ``_load`` which has been overriden by this base class
    '''

    params = (('headers', True), ('separator', ','),)

    def start(self):
        super(CSVDataBase, self).start()

        if hasattr(self.p.dataname, 'readline'):
            self.f = self.p.dataname
        else:
            # Let an exception propagate to let the caller know
            self.f = open(self.p.dataname, 'rb')

        if self.p.headers:
            self.f.readline()  # skip the headers

        self.separator = bytes(self.p.separator)

    def stop(self):
        if self.f is not None:
            self.f.close()
            self.f = None

    def _load(self):
        if self.f is None:
            return False

        # Let an exception propagate to let the caller know
        line = self.f.readline()

        if not line:
            return False

        line = line.rstrip(b'\r\n')
        linetokens = line.split(self.separator)
        return self._loadline(linetokens)


class CSVFeedBase(FeedBase):
    params = (('basepath', ''),) + CSVDataBase.params._gettuple()

    def _getdata(self, dataname, **kwargs):
        return self.DataCls(dataname=self.p.basepath + dataname,
                            **self.p._getkwargs())

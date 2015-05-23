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

import datetime
import os.path

import six

from . import dataseries
from . import metabase
from . import TimeFrame
from .utils import date2num


class MetaDataBase(dataseries.OHLCDateTime.__class__):
    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaDataBase, cls).dopreinit(_obj, *args, **kwargs)

        # Find the owner and store it
        _obj._feed = metabase.findowner(_obj, FeedBase)

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaDataBase, cls).dopostinit(_obj, *args, **kwargs)

        _obj._name = _obj.p.name
        _obj._compression = _obj.p.compression
        _obj._timeframe = _obj.p.timeframe

        if _obj.p.sessionend is None:
            _obj.p.sessionend = datetime.time(23, 59, 59)

        if isinstance(_obj.p.fromdate, datetime.date):
            # push it to the end of the day, or else intraday
            # values before the end of the day would be gone
            _obj.p.fromdate = datetime.datetime.combine(
                _obj.p.fromdate, _obj.p.sessionend)

        if isinstance(_obj.p.todate, datetime.date):
            # push it to the end of the day, or else intraday
            # values before the end of the day would be gone
            _obj.p.todate = datetime.datetime.combine(
                _obj.p.todate, _obj.p.sessionend)

        _obj.fromdate = date2num(_obj.p.fromdate)
        _obj.todate = date2num(_obj.p.todate)

        # hold datamaster points corresponding to own
        _obj.mlen = list()

        return _obj, args, kwargs


class DataBase(six.with_metaclass(MetaDataBase, dataseries.OHLCDateTime)):
    _feed = None

    params = (('dataname', None),
              ('fromdate', datetime.datetime.min),
              ('todate', datetime.datetime.max),
              ('name', ''),
              ('compression', 1),
              ('timeframe', TimeFrame.Days),
              ('sessionend', None))

    def getfeed(self):
        return self._feed

    def start(self):
        pass

    def stop(self):
        pass

    def advance(self, datamaster=None):
        # Need intercepting this call to support datas with
        # different lengths (timeframes)
        self.lines.advance()

        if datamaster:
            if self.lines.datetime[0] > datamaster.lines.datetime[0]:
                self.lines.rewind()
            else:
                self.mlen.append(len(datamaster))

    def next(self, datamaster=None):
        if len(self) == self.buflen():
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

            return True

        return False

    def _load(self):
        return False


class FeedBase(six.with_metaclass(metabase.MetaParams, object)):
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

        data = self._getdata(dataname, **kwargs)
        data._name = name
        self.datas.append(data)
        return data

    def _getdata(self, dataname, **kwargs):
        for pname, pvalue in self.p._getitems():
            kwargs.setdefault(pname, getattr(self.p, pname))

        return self.DataCls(data=dataname, **kwargs)


class MetaCSVDataBase(DataBase.__class__):
    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaCSVDataBase, cls).dopostinit(_obj, *args, **kwargs)

        if not _obj._name:
            _obj._name, _ = os.path.splitext(os.path.basename(_obj.p.dataname))

        return _obj, args, kwargs


class CSVDataBase(six.with_metaclass(MetaCSVDataBase, DataBase)):
    params = (('headers', True), ('separator', ','),)

    def start(self):
        if hasattr(self.p.dataname, 'readline'):
            self.f = self.p.dataname
        else:
            # Let an exception propagate to let the caller know
            self.f = open(self.p.dataname, 'rb')

        if self.p.headers:
            self.f.readline()  # skip the headers

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

        line = line.rstrip(six.b('\r\n'))
        linetokens = line.split(six.b(self.p.separator))
        return self._loadline(linetokens)


class CSVFeedBase(FeedBase):
    params = (('basepath', ''),) + CSVDataBase.params._gettuple()

    def _getdata(self, dataname, **kwargs):
        return self.DataCls(dataname=self.p.basepath + dataname,
                            **self.p._getkwargs())

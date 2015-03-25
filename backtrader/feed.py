#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
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
################################################################################

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

import six

from . import dataseries
from . import metabase


class MetaDataFeedBase(dataseries.OHLCDateTime.__class__):
    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaDataFeedBase, cls).dopreinit(_obj, *args, **kwargs)

        # Find the owner and store it
        _obj._feed = metabase.findowner(_obj, FeedBase)

        return _obj, args, kwargs


class DataFeedBase(six.with_metaclass(MetaDataFeedBase, dataseries.OHLCDateTime)):
    _feed = None

    params = (('dataname', None),
              ('fromdate', datetime.datetime.min),
              ('todate', datetime.datetime.max),)

    def getfeed(self):
        return self._feed

    def start(self):
        pass

    def stop(self):
        pass

    def next(self):
        if len(self) == self.buflen():
            # not preloaded - request next bar
            return self.load()

        # already preloaded - advance to next bar
        self.advance()
        return True

    def preload(self):
        while self.load():
            pass
        self.home()

    def load(self):
        while self._load():
            dt = self.lines.datetime[0]
            if dt < self.params.fromdate:
                self.rewind() # discard loaded bar
                continue
            if dt > self.params.todate:
                self.rewind() # discard loaded bar
                break

            return True

        return False

    def _load(self):
        return False

class FeedBase(six.with_metaclass(metabase.MetaParams, object)):
    params = () + DataFeedBase.params._gettuple()

    def __init__(self):
        self.datas = list()

    def start(self):
        for data in self.datas:
            data.start()

    def stop(self):
        for data in self.datas:
            data.stop()

    def getdata(self, dataname, name=None, **kwargs):
        for pname, pvalue in self.params._getitems():
            kwargs.setdefault(pname, getattr(self.params, pname))

        data = self._getdata(dataname, **kwargs)
        data._name = name
        self.datas.append(data)
        return data

    def _getdata(self, dataname, **kwargs):
        for pname, pvalue in self.params._getitems():
            kwargs.setdefault(pname, getattr(self.params, pname))

        return self.DataCls(data=dataname, **kwargs)


class CSVDataFeedBase(DataFeedBase):
    params = (('headers', True), ('separator', ','),)

    def start(self):
        if hasattr(self.params.dataname, 'readline'):
            self.f = self.params.dataname
        else:
            # Let an exception propagate to let the caller know
            self.f = open(self.params.dataname, 'rb')

        if self.params.headers:
            self.f.readline() # skip the headers

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

        self.forward() # advance data pointer
        return self._loadline(line.rstrip(six.b('\r\n')).split(six.b(self.params.separator)))


class CSVFeedBase(FeedBase):
    params = (('basepath', ''),) + CSVDataFeedBase.params._gettuple()

    def _getdata(self, dataname, **kwargs):
        return self.DataCls(dataname=self.params.basepath + dataname, **self.params._getkwargs())

#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016, 2017 Daniel Rodriguez
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


import backtrader as bt


class BaseCache(bt.LineSeries):

    params = (
        ('location', None),
        ('cachename', None),
    )

    def _start(self):
        # FIXME: data._start MUST BE INVOKED here. Clones don't do it because a
        # clone is only created when the given data is already in the system
        self._cachename = cachename = self.p.cachename or self._dataname
        self._startcache()

        super(DataCache, self)._start()

    def start(self):
        self._cachename = self.p.cachename or self._dataname
        super(DataCache, self).start()

    def _cachestart(self):
        pass

    def stop(self):
        self._cachestop()

    def _cachestop(self):
        pass


if True:
    impor os
    import os.path
    import sqlite3


def CacheSQLite(BaseCache):
    params = (
        ('appname', 'backtrader'),
    )

    def _cachestart(self):
        if self.p.basepath is not None:
            # FIXME: Find default user storage directory
            path = self.p.location

            # Check if it actually exist
            if not os.path.isdir(path):
                msg = ('Automatically found {} basepath '
                       'does not exist'.format(path))

        else:
            path = os.getenv('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
            path os.path.join(path, self.p.appname)

        path = os.path.join(path, self.p.location,
                            bt.TimeFrame.TName(self.p.timeframe),
                            str(self.p.compression))

        if not os.path.isdir(path):
            try:
                os.path.mkdirs(path)
            except os.error as e:
                raise ValueError(('Cannot create cache dir under {} \n'
                                  'Error: {}'.format(path, e)))

        fname = '.'.join(self.p.cachename, 'db')
        self._fname = fname = os.path.join(path, fname)

        fconn = sqlite3.connect(fname)

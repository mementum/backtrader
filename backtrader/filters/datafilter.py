#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
# Copyright (C) 2026 Dennis Hansen
#
# This file is part of slim-backtrader, a modified version of backtrader.
# Modified in 2026 by Dennis Hansen. See changelog.txt for the changes.
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

import backtrader as bt


class DataFilter(bt.AbstractDataBase):
    """
    This class filters out bars from a given data source. In addition to the
    standard parameters of a DataBase it takes a ``funcfilter`` parameter which
    can be any callable

    Logic:

      - ``funcfilter`` will be called with the underlying data source

        It can be any callable

        - Return value ``True``: current data source bar values will used
        - Return value ``False``: current data source bar values will discarded
    """

    params = (("funcfilter", None),)

    def _startinner(self):
        """Start the wrapped feed the way cerebro starts a feed of its own.

        The inner feed is never handed to cerebro, so nothing else gives it an
        environment or runs the second half of its start-up: _start_finish()
        is what sets _tzinput and the trading calendar, and plain start() does
        not reach it.
        """
        self.p.dataname.setenvironment(self._env)
        self.p.dataname._start()
        # Copied by name: the inner feed may carry lines this one has not
        # (YahooFinanceCSVData's adjclose, an option feed's bid and ask)
        inner = self.p.dataname.lines
        self._copylines = [
            (self.lines[i], getattr(inner, alias))
            for i, alias in enumerate(self.lines.getlinealiases())
        ]

    def start(self):
        super(DataFilter, self).start()
        # Started here rather than lazily from _load(). _load() used to ask
        # "not len(dataname)" to mean "not started yet", but len() is also 0
        # immediately after home() rewinds a preloaded feed - so preloading
        # restarted the source, reopened the file it had just closed, and
        # delivered every bar a second time.
        self._startinner()

    def stop(self):
        super().stop()
        # Started by _startinner, so stopped here: cerebro never sees the
        # inner feed, and a feed left running keeps its file open
        self.p.dataname.stop()

    def preload(self):
        if len(self.p.dataname) == self.p.dataname.buflen():
            # if data is not preloaded .... do it
            self.p.dataname.preload()
            self.p.dataname.home()

        # Copy timeframe from data after start (some sources do autodetection)
        self.p.timeframe = self._timeframe = self.p.dataname._timeframe
        self.p.compression = self._compression = self.p.dataname._compression

        super(DataFilter, self).preload()

    def _load(self):
        # Tell underlying source to get next data
        while self.p.dataname.next():
            # Try to load the data from the underlying source
            if not self.p.funcfilter(self.p.dataname):
                continue

            for mine, theirs in self._copylines:
                mine[0] = theirs[0]

            return True

        return False  # no more data from underlying source

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

from .. import Observer
from ..trade import Trade


class Trades(Observer):
    lines = ('pnlplus', 'pnlminus')

    plotinfo = dict(plot=True, subplot=True,
                    plotname='Trades - Net Profit/Loss',
                    plothlines=[0.0])

    plotlines = dict(
        pnlplus=dict(_name='Positive',
                     marker='o', color='blue',
                     markersize=8.0, fillstyle='full'),
        pnlminus=dict(_name='Negative',
                      marker='o', color='red',
                      markersize=8.0, fillstyle='full')
    )

    def __init__(self):

        self.trades = 0

        self.trades_long = 0
        self.trades_short = 0

        self.trades_plus = 0
        self.trades_minus = 0

        self.trades_plus_gross = 0
        self.trades_minus_gross = 0

        self.trades_win = 0
        self.trades_win_max = 0
        self.trades_win_min = 0

        self.trades_loss = 0
        self.trades_loss_max = 0
        self.trades_loss_min = 0

        self.trades_length = 0
        self.trades_length_max = 0
        self.trades_length_min = 0

    def next(self):
        for trade in self._owner._tradespending:
            if trade.data is not self.data:
                continue

            if not trade.isclosed:
                continue

            if trade.pnl >= 0:
                self.lines.pnlplus[0] = trade.pnl
            else:
                self.lines.pnlminus[0] = trade.pnl

            if False:
                self.trades_long += trade.long
                self.trades_short += not trade.long

                self.trades_plus += trade.pnl > 0
                self.trades_minus += trade.pnl < 0

                self.trades_plus_gross += trade.pnlcomm > 0
                self.trades_minus_gross += trade.pnlcomm < 0

                if trade.pnl >= 0:
                    w = self.trades_win * self.trades + trade.pnl
                    self.trades_win = w / (self.trades + 1)
                    self.trades_win_max = max(self.trades_win_max, trade.pnl)
                    self.trades_win_min = min(self.trades_win_min, trade.pnl)
                elif trade.pnl < 0:
                    l = self.trades_loss * self.trades + trade.pnl
                    self.trades_loss = l / (self.trades + 1)
                    self.trades_loss_max = max(self.trades_loss_max, trade.pnl)
                    self.trades_loss_min = min(self.trades_loss_min, trade.pnl)

                l = self.trades_length * self.trades + trade.barlen
                self.trades_length = l / (self.trades + 1)
                self.trades_length_max = max(self.trades_length_max, trade.barlen)
                self.trades_length_min = min(self.trades_length_min, trade.barlen)

                self.trades += 1

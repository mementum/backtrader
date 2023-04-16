#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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

import math

import backtrader as bt


class MTradeObserver(bt.observer.Observer):
    lines = ('Id_0', 'Id_1', 'Id_2')

    plotinfo = dict(plot=True, subplot=True, plotlinelabels=True)

    plotlines = dict(
        Id_0=dict(marker='*', markersize=8.0, color='lime', fillstyle='full'),
        Id_1=dict(marker='o', markersize=8.0, color='red', fillstyle='full'),
        Id_2=dict(marker='s', markersize=8.0, color='blue', fillstyle='full')
    )

    def next(self):
        for trade in self._owner._tradespending:

            if trade.data is not self.data:
                continue

            if not trade.isclosed:
                continue

            self.lines[trade.tradeid][0] = trade.pnlcomm

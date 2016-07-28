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

import math

from ..observer import Observer


class BuySell(Observer):
    '''
    This observer keeps track of the individual buy/sell orders (individual
    executions) and will plot them on the chart along the data around the
    execution price level

    Params: None
    '''
    lines = ('buy', 'sell',)

    plotinfo = dict(plot=True, subplot=False, plotlinelabels=True)
    plotlines = dict(
        buy=dict(marker='^', markersize=8.0, color='lime', fillstyle='full'),
        sell=dict(marker='v', markersize=8.0, color='red', fillstyle='full')
    )

    def next(self):
        buy = list()
        sell = list()

        for order in self._owner._orderspending:
            if order.data is not self.data or not order.executed.size:
                continue

            if order.isbuy():
                buy.append(order.executed.price)
            else:
                sell.append(order.executed.price)

        # Take into account replay ... something could already be in there
        # Write down the average buy/sell price

        # BUY
        curbuy = self.lines.buy[0]
        if curbuy != curbuy:  # NaN
            curbuy = 0.0
            self.curbuylen = curbuylen = 0
        else:
            curbuylen = self.curbuylen

        buyops = (curbuy + math.fsum(buy))
        buylen = curbuylen + len(buy)
        self.lines.buy[0] = buyops / float(buylen or 'NaN')

        # Update buylen values
        curbuy = buyops
        self.curbuylen = buylen

        # SELL
        cursell = self.lines.sell[0]
        if cursell != cursell:  # NaN
            cursell = 0.0
            self.curselllen = curselllen = 0
        else:
            curselllen = self.curselllen

        sellops = (cursell + math.fsum(sell))
        selllen = curselllen + len(sell)
        self.lines.sell[0] = sellops / float(selllen or 'NaN')

        # Update selllen values
        cursell = sellops
        self.curselllen = selllen

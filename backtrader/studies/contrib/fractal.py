#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-

###############################################################################
#
# Copyright (C) 2017 Christoph Giese <cgi1> (based on backtrader from Daniel Rodriguez)
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

class Fractal(Indicator):

    '''
    References:
        [Ref 1] http://www.investopedia.com/articles/trading/06/fractals.asp
    
    '''
    
    lines = ('fractal_bearish', 'fractal_bullish')

    plotinfo = dict(subplot=False, plotlinelabels=False, plot=True)

    plotlines = dict(
        fractal_bearish=dict(marker='^', markersize=4.0, color='lightblue',
                 fillstyle='full', ls=''),
        fractal_bullish=dict(marker='v', markersize=4.0, color='lightblue',
                  fillstyle='full', ls='')
    )
    params = (
        ('bardist', 0.015),  # distance to max/min in absolute perc
    )

    def log(self, txt, dt=None):
        """ Logging function for this indicator"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def next(self):

        if len(self.data) < 5:
            self.log("Not enough data yet. (Min 5 bars).")
            return

        shift_to_potential_fractal = 2

        # A bearish turning point occurs when there is a pattern
        # with the highest high in the middle and two lower highs on each side. [Ref 1]

        last_five_highs = [self.datas[0].high[-4], self.datas[0].high[-3], self.datas[0].high[-2],
                           self.datas[0].high[-1], self.datas[0].high[0]]

        max_val = max(last_five_highs)
        max_idx = last_five_highs.index(max_val)

        if max_idx == shift_to_potential_fractal:

            self.log("Found bearish fractal with high (%.2f)!" % max_val)
            self.lines.fractal_bearish[-2] = max_val * (1 + self.p.bardist)
        
        # A bullish turning point occurs when there is a pattern
        # with the lowest low in the middle and two higher lowers on each side. [Ref 1]


        last_five_lows = [self.datas[0].low[-4], self.datas[0].low[-3], self.datas[0].low[-2],
                          self.datas[0].low[-1], self.datas[0].low[0]]
        min_val = min(last_five_lows)
        min_idx = last_five_lows.index(min_val)

        if min_idx == shift_to_potential_fractal:
            self.log("Found bullish fractal with low (%.2f)!" % min_val)
            self.l.fractal_bullish[-2] = min_val * (1 - self.p.bardist)

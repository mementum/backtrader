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

import sys

from backtrader import Analyzer
from backtrader.utils import AutoOrderedDict, AutoDict


class TradeAnalyzer(Analyzer):
    def start(self):
        self.trades = AutoOrderedDict()

    def stop(self):
        self.trades._close()

    def notify_trade(self, trade):
        if trade.justopened:
            # Trade just opened
            self.trades.total.total += 1
            self.trades.total.open += 1

        elif trade.status == trade.Closed:
            res = AutoDict()
            # Trade just closed

            won = res.won = trade.pnlcomm >= 0.0
            lost = res.lost = not res.won
            tlong = res.tlong = trade.long
            tshort = res.tshort = not trade.long

            trades = self.trades

            trades.total.open -= 1
            trades.total.closed += 1

            for wlname in ['won', 'lost']:
                wl = res[wlname]

                trades.total[wlname] += wl

                trades.streak[wlname].current *= wl
                trades.streak[wlname].current += wl

                ls = trades.streak[wlname].longest or 0
                trades.streak[wlname].longest = \
                    max(ls, trades.streak[wlname].current)

            trpnl = trades.pnl
            trpnl.gross.total += trade.pnl
            trpnl.gross.average = trades.pnl.gross.total / trades.total.closed
            trpnl.net.total += trade.pnlcomm
            trpnl.net.average = trades.pnl.net.total / trades.total.closed

            # Long/Short statistics
            for tname in ['long', 'short']:
                trls = trades[tname]
                ls = res['t' + tname]

                trls.total += ls  # long.total / short.total
                trls.pnl.total += trade.pnlcomm * ls
                trls.pnl.average = trls.pnl.total / (trls.total or 1.0)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]
                    pnlcomm = trade.pnlcomm * wl * ls

                    trls[wlname] += wl * ls  # long.won / short.won

                    trls.pnl[wlname].total += pnlcomm
                    trls.pnl[wlname].average = \
                        trls.pnl[wlname].total / (trls[wlname] or 1.0)

                    wm = trls.pnl[wlname].max or 0.0
                    func = max if wlname == 'won' else min
                    trls.pnl[wlname].max = func(wm, pnlcomm)

            # Length
            trades.len.total += trade.barlen
            trades.len.average = trades.len.total / trades.total.closed
            ml = trades.len.max or 0
            trades.len.max = max(ml, trade.barlen)

            ml = trades.len.min or sys.maxint
            trades.len.min = min(ml, trade.barlen)

            # Length Won/Lost
            for wlname in ['won', 'lost']:
                trwl = trades.len[wlname]
                wl = res[wlname]

                trwl.total += trade.barlen * wl
                trwl.average = trwl.total / (trades.total[wlname] or 1.0)

                m = trwl.max or 0
                trwl.max = max(m, trade.barlen * wl)
                if trade.barlen * wl:
                    m = trwl.min or sys.maxint
                    trwl.min = min(m, trade.barlen * wl)

            # Length Long/Short
            for lsname in ['long', 'short']:
                trls = trades.len[lsname]  # trades.len.long
                ls = res['t' + lsname]  # tlong/tshort

                barlen = trade.barlen * ls

                trls.total += barlen  # trades.len.long.total
                total_ls = trades[lsname].total   # trades.long.total
                trls.average = trls.total / (total_ls or 1.0)

                # max/min
                m = trls.max or 0
                trls.max = max(m, barlen)
                m = trls.min or sys.maxint
                trls.min = min(m, barlen or m)

                for wlname in ['won', 'lost']:
                    wl = res[wlname]  # won/lost

                    barlen2 = trade.barlen * ls * wl

                    trls_wl = trls[wlname]  # trades.len.long.won
                    trls_wl.total += barlen2  # trades.len.long.won.total

                    trls_wl.average = \
                        trls_wl.total / (trades[lsname][wlname] or 1.0)

                    # max/min
                    m = trls_wl.max or 0
                    trls_wl.max = max(m, barlen2)
                    m = trls_wl.min or sys.maxint
                    trls_wl.min = min(m, barlen2 or m)

    def get_analysis(self):
        return self.trades

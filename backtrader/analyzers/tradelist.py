from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import collections

import backtrader as bt
from backtrader import Order, Position

class TradeList(bt.Analyzer):
    params = (
        ('headers', False),
        ('_pfheaders', ('ref', 'ticker', 'size', 'nbars', 'pricein', 'priceout', 'chng%', 'pnl', 'pnl%', 'mfe%', 'mae%')),
    )

    def start(self):
        super(TradeList, self).start()
        if self.p.headers:
            self.rets[self.p._pfheaders[0]] = [list(self.p._pfheaders[1:])]

    def stop(self):
        super(TradeList, self).stop()

    def __init__(self):
        self.cumprofit = 0.0

    def notify_trade(self, trade):
        if trade.isclosed:
            brokervalue = self.strategy.broker.getvalue()

            dir = 'short'
            if trade.history[0].event.size > 0: dir = 'long'

            pricein = trade.history[len(trade.history)-1].status.price
            priceout = trade.history[len(trade.history)-1].event.price
            datein = bt.num2date(trade.history[0].status.dt)
            dateout = bt.num2date(trade.history[len(trade.history)-1].status.dt)
            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()

            pcntchange = 100 * priceout / pricein - 100
            pnl = trade.history[len(trade.history)-1].status.pnlcomm
            pnlpcnt = 100 * pnl / brokervalue
            barlen = trade.history[len(trade.history)-1].status.barlen
            pbar = pnl / barlen
            self.cumprofit += pnl

            size = value = 0.0
            for record in trade.history:
                if abs(size) < abs(record.status.size):
                    size = record.status.size
                    value = record.status.value

            highest_in_trade = max(trade.data.high.get(ago=0, size=barlen+1))
            lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen+1))
            hp = 100 * (highest_in_trade - pricein) / pricein
            lp = 100 * (lowest_in_trade - pricein) / pricein
            if dir == 'long':
                mfe = hp
                mae = lp
            if dir == 'short':
                mfe = -lp
                mae = -hp

            self.rets[trade.ref] = [[trade.data._name, size, barlen, round(pricein, 3), round(priceout, 3), round(pcntchange, 2), round(pnl, 2), round(pnlpcnt, 2), round(mfe, 2), round(mae, 2)]]
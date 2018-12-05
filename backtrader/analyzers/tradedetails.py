from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import collections

import backtrader as bt

class TradeDetails(bt.Analyzer):
    params = (
        ('headers', False),
        ('_pfheaders', ('ref', 'ticker', 'size', 'nbars', 'datein', 'dateout', 'pnl', 'cpnl', 'mfe', 'mae')),
    )

    def start(self):
        super(TradeDetails, self).start()
        if self.p.headers:
            self.rets[self.p._pfheaders[0]] = [list(self.p._pfheaders[1:])]

    def stop(self):
        super(TradeDetails, self).stop()

    def __init__(self):
        self.cumprofit = 0.0

    def notify_trade(self, trade):
        if trade.isclosed:
            brokervalue = self.strategy.broker.getvalue()

            dir = 'SHORT'
            if trade.long: dir = 'LONG'

            if trade.historyon:
                pricein = trade.history[len(trade.history)-1].status.price
                # priceout = trade.history[len(trade.history)-1].event.price
                datein = bt.num2date(trade.history[0].status.dt)
                dateout = bt.num2date(trade.history[len(trade.history)-1].status.dt)
                pnl = trade.history[len(trade.history)-1].status.pnlcomm
                barlen = trade.history[len(trade.history)-1].status.barlen
            else:
                # we can calculate MFE/MAE using average price just as well (using trade.price) for trades that have not increased position 
                # it'll be the same as price open, alternatively trade object can be extended to include priceopen and priceclosed properties
                # pricein = trade.priceopen
                pricein = trade.price
                # priceout = trade.priceclose
                datein = trade.open_datetime()
                dateout = trade.close_datetime()
                pnl = trade.pnlcomm
                barlen = trade.barlen

            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()

            pnlpcnt = 100 * pnl / brokervalue
            # pbar = pnl / barlen
            self.cumprofit += pnl

            # MFE/MAE calculation is only possible if we have access to full data history, this is better than just failing if exactbars is True
            if self.strategy.cerebro._exactbars:
                mfe = 0
                mae = 0
            else:
                highest_in_trade = max(trade.data.high.get(ago=0, size=barlen+1))
                lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen+1))
                hp = 100 * (highest_in_trade - pricein) / pricein
                lp = 100 * (lowest_in_trade - pricein) / pricein
                if dir == 'LONG':
                    mfe = hp
                    mae = lp
                if dir == 'SHORT':
                    mfe = -lp
                    mae = -hp

            self.rets[trade.ref] = [[trade.data._name, dir, barlen, datein, dateout, round(pnl, 3), round(self.cumprofit, 3), round(mfe, 3), round(mae, 3)]]
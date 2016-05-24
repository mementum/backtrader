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

import collections

from .utils.py3 import with_metaclass

from .comminfo import CommInfoBase
from .position import Position
from .metabase import MetaParams
from .order import Order, BuyOrder, SellOrder


class BrokerBase(with_metaclass(MetaParams, object)):
    params = (
        ('commission', CommInfoBase(percabs=True)),
    )

    def __init__(self):
        self.comminfo = dict()
        self.init()

    def init(self):
        # called from init and from start
        if None not in self.comminfo:
            self.comminfo = dict({None: self.p.commission})

    def start(self):
        self.init()

    def stop(self):
        pass

    def getcommissioninfo(self, data):
        if data._name in self.comminfo:
            return self.comminfo[data._name]

        return self.comminfo[None]

    def setcommission(self,
                      commission=0.0, margin=None, mult=1.0,
                      commtype=None, percabs=True, stocklike=False,
                      name=None):

        comm = CommInfoBase(commission=commission, margin=margin, mult=mult,
                            commtype=commtype, stocklike=stocklike,
                            percabs=percabs)
        self.comminfo[name] = comm

    def addcommissioninfo(self, comminfo, name=None):
        self.comminfo[name] = comminfo

    def getcash(self):
        raise NotImplementedError

    def getvalue(self, datas=None):
        raise NotImplementedError

    def getposition(self, data):
        raise NotImplementedError

    def submit(self, order):
        raise NotImplementedError

    def cancel(self, order):
        raise NotImplementedError

    def buy(self, owner, data, size, price=None, plimit=None, exectype=None,
            valid=None, tradeid=0, **kwargs):

        raise NotImplementedError

    def sell(self, owner, data, size, price=None, plimit=None, exectype=None,
             valid=None, tradeid=0, **kwargs):

        raise NotImplementedError

    def next(self):
        pass


class BrokerBack(BrokerBase):
    '''Broker Simulator

      Parameters:

        Note: use the setXXXX to set the value after instance creation

        - ``cash`` (default: 10000): starting cash

        - ``commission`` (default: CommInfoBase(percabs=True))
          base commission scheme which applies to all assets

        - ``checksubmit`` (default: True)
          check margin/cash before accepting an order into the system

        - ``eosbar`` (default: False):
          With intraday bars consider a bar with the same ``time`` as the end
          of session to be the end of the session. This is not usually the
          case, because some bars (final auction) are produced by many
          exchanges for many products for a couple of minutes after the end of
          the session
    '''
    params = (
        ('cash', 10000.0),
        ('checksubmit', True),
        ('eosbar', False),
    )

    def init(self):
        super(BrokerBack, self).init()
        self.startingcash = self.cash = self.p.cash

        self.orders = list()  # will only be appending
        self.pending = collections.deque()  # popleft and append(right)

        self.positions = collections.defaultdict(Position)
        self.notifs = collections.deque()

        self.submitted = collections.deque()

    def get_notification(self):
        try:
            return self.notifs.popleft()
        except IndexError:
            pass

        return None

    def seteosbar(self, eosbar):
        self.p.eosbar = eosbar

    def getcash(self):
        return self.cash

    def setcash(self, cash):
        self.startingcash = self.cash = self.p.cash = cash

    def cancel(self, order):
        try:
            self.pending.remove(order)
        except ValueError:
            # If the list didn't have the element we didn't cancel anything
            return False

        order.cancel()
        self.notify(order)
        return True

    def getvalue(self, datas=None):
        pos_value = 0.0

        for data in datas or self.positions:
            comminfo = self.getcommissioninfo(data)
            position = self.positions[data]
            pos_value += comminfo.getvalue(position, data.close[0])

        return self.cash + pos_value

    def getposition(self, data):
        return self.positions[data]

    def orderstatus(self, order):
        try:
            o = self.orders.index(order)
        except ValueError:
            o = order

        return o.status

    def submit(self, order):
        if self.p.checksubmit:
            order.submit()
            self.submitted.append(order)
            self.orders.append(order)
            self.notify(order)
        else:
            self.submit_accept(order)

        return order

    def check_submitted(self):
        cash = self.cash
        positions = dict()

        while self.submitted:
            order = self.submitted.popleft()
            comminfo = self.getcommissioninfo(order.data)

            position = positions.setdefault(
                order.data, self.positions[order.data].clone())

            # pseudo-execute the order to get the remaining cash after exec
            cash = self._execute(order, cash=cash, position=position)

            if cash >= 0.0:
                self.submit_accept(order)
                continue

            order.margin()
            self.notify(order)

    def submit_accept(self, order):
        order.pannotated = None
        order.accept()
        self.pending.append(order)
        self.notify(order)

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0,
            **kwargs):

        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)

        return self.submit(order)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0,
             **kwargs):

        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid)

        order.addinfo(**kwargs)

        return self.submit(order)

    def _execute(self, order, dt=None, price=None, cash=None, position=None):
        # Orders are fully executed, get operation size
        size = order.executed.remsize

        # Get comminfo object for the data
        comminfo = self.getcommissioninfo(order.data)

        # Adjust position with operation size
        if dt is not None:
            # Real execution with date
            position = self.positions[order.data]
            pprice_orig = position.price

            psize, pprice, opened, closed = position.pseudoupdate(size, price)

            # if part/all of a position has been closed, then there has been
            # a profitandloss ... record it
            pnl = comminfo.profitandloss(-closed, pprice_orig, price)
            cash = self.cash
        else:
            pnl = 0
            price = pprice_orig = order.created.price
            psize, pprice, opened, closed = position.update(size, price)

        # "Closing" totally or partially is possible. Cash may be re-injected
        if closed:
            # Adjust to returned value for closed items & acquired opened items
            closedvalue = comminfo.getoperationcost(closed, pprice_orig)
            cash += closedvalue + pnl * comminfo.stocklike
            # Calculate and substract commission
            closedcomm = comminfo.getcommission(closed, price)
            cash -= closedcomm

            if dt is not None:
                # Cashadjust closed contracts: prev close vs exec price
                # The operation can inject or take cash out
                cash += comminfo.cashadjust(-closed,
                                            position.adjbase,
                                            price)

                # Update system cash
                self.cash = cash
        else:
            closedvalue = closedcomm = 0.0

        popened = opened
        if opened:
            openedvalue = comminfo.getoperationcost(opened, price)
            cash -= openedvalue

            openedcomm = comminfo.getcommission(opened, price)
            cash -= openedcomm

            if cash < 0.0:
                # execution is not possible - nullify
                opened = 0
                openedvalue = openedcomm = 0.0

            elif dt is not None:  # real execution
                if abs(psize) > abs(opened):
                    # some futures were opened - adjust the cash of the
                    # previously existing futures to the operation price and
                    # use that as new adjustment base, because it already is
                    # for the new futures At the end of the cycle the
                    # adjustment to the close price will be done for all open
                    # futures from a common base price with regards to the
                    # close price
                    adjsize = psize - opened
                    cash += comminfo.cashadjust(adjsize,
                                                position.adjbase, price)

                # record adjust price base for end of bar cash adjustment
                position.adjbase = price

                # update system cash - checking if opened is still != 0
                self.cash = cash
        else:
            openedvalue = openedcomm = 0.0

        if dt is None:
            # return cash from pseudo-execution
            return cash

        execsize = closed + opened

        if execsize:
            # Confimrm the operation to the comminfo object
            comminfo.confirmexec(execsize, price)

            # do a real position update if something was executed
            position.update(execsize, price)

            # Execute and notify the order
            order.execute(dt, execsize, price,
                          closed, closedvalue, closedcomm,
                          opened, openedvalue, openedcomm,
                          comminfo.margin, pnl,
                          psize, pprice)

            order.addcomminfo(comminfo)

            self.notify(order)

        if popened and not opened:
            # opened was not executed - not enough cash
            order.margin()
            self.notify(order)

    def notify(self, order):
        self.notifs.append(order.clone())

    def _try_exec_close(self, order, pclose):
        if len(order.data) > order.plen:
            dt0 = order.data.datetime[0]

            if dt0 > order.dteos or (self.p.eosbar and dt0 == order.dteos):
                # past the end of session or right at it and eosbar is True
                if order.pannotated and dt0 != order.dteos:
                    execdt = order.data.datetime[-1]
                    execprice = order.pannotated
                else:
                    execdt = dt0
                    execprice = pclose

                self._execute(order, execdt, price=execprice)

                return

        # If no exexcution has taken place ... annotate the closing price
        order.pannotated = pclose

    def _try_exec_limit(self, order, popen, phigh, plow, plimit):
        if order.isbuy():
            if plimit >= popen:
                # open smaller/equal than requested - buy cheaper
                self._execute(order, order.data.datetime[0], price=popen)
            elif plimit >= plow:
                # day low below req price ... match limit price
                self._execute(order, order.data.datetime[0], price=plimit)

        else:  # Sell
            if plimit <= popen:
                # open greater/equal than requested - sell more expensive
                self._execute(order, order.data.datetime[0], price=popen)
            elif plimit <= phigh:
                # day high above req price ... match limit price
                self._execute(order, order.data.datetime[0], price=plimit)

    def _try_exec_stop(self, order, popen, phigh, plow, pcreated):
        if order.isbuy():
            if popen >= pcreated:
                # price penetrated with an open gap - use open
                self._execute(order, order.data.datetime[0], price=popen)
            elif phigh >= pcreated:
                # price penetrated during the session - use trigger price
                self._execute(order, order.data.datetime[0], price=pcreated)

        else:  # Sell
            if popen <= pcreated:
                # price penetrated with an open gap - use open
                self._execute(order, order.data.datetime[0], price=popen)
            elif plow <= pcreated:
                # price penetrated during the session - use trigger price
                self._execute(order, order.data.datetime[0], price=pcreated)

    def _try_exec_stoplimit(self, order,
                            popen, phigh, plow, pclose,
                            pcreated, plimit):
        if order.isbuy():
            if popen >= pcreated:
                order.triggered = True
                # price penetrated with an open gap
                if plimit >= popen:
                    self._execute(order, order.data.datetime[0], price=popen)
                elif plimit >= plow:
                    # execute in same bar
                    self._execute(order, order.data.datetime[0], price=plimit)

            elif phigh >= pcreated:
                # price penetrated upwards during the session
                order.triggered = True
                # can calculate execution for a few cases - datetime is fixed
                dt = order.data.datetime[0]
                if popen > pclose:
                    if plimit >= pcreated:
                        self._execute(order, dt, price=pcreated)
                    elif plimit >= pclose:
                        self._execute(order, dt, price=plimit)
                else:  # popen < pclose
                    if plimit >= pcreated:
                        self._execute(order, dt, price=pcreated)
        else:  # Sell
            if popen <= pcreated:
                # price penetrated downwards with an open gap
                order.triggered = True
                if plimit <= popen:
                    self._execute(order, order.data.datetime[0], price=popen)
                elif plimit <= phigh:
                    # execute in same bar
                    self._execute(order, order.data.datetime[0], price=plimit)

            elif plow <= pcreated:
                # price penetrated downwards during the session
                order.triggered = True
                # can calculate execution for a few cases - datetime is fixed
                dt = order.data.datetime[0]
                if popen <= pclose:
                    if plimit <= pcreated:
                        self._execute(order, dt, price=pcreated)
                    elif plimit <= pclose:
                        self._execute(order, dt, price=plimit)
                else:
                    # popen > pclose
                    if plimit <= pcreated:
                        self._execute(order, dt, price=pcreated)

    def _try_exec(self, order):
        data = order.data

        popen = data.tick_open or data.open[0]
        phigh = data.tick_high or data.high[0]
        plow = data.tick_low or data.low[0]
        pclose = data.tick_close or data.close[0]

        pcreated = order.created.price
        plimit = order.created.pricelimit

        if order.exectype == Order.Market:
            self._execute(order, data.datetime[0], price=popen)

        elif order.exectype == Order.Close:
            self._try_exec_close(order, pclose)

        elif order.exectype == Order.Limit:
            self._try_exec_limit(order, popen, phigh, plow, pcreated)

        elif order.exectype == Order.StopLimit and order.triggered:
            self._try_exec_limit(order, popen, phigh, plow, plimit)

        elif order.exectype == Order.Stop:
            self._try_exec_stop(order, popen, phigh, plow, pcreated)

        elif order.exectype == Order.StopLimit:
            self._try_exec_stoplimit(order,
                                     popen, phigh, plow, pclose,
                                     pcreated, plimit)

    def next(self):
        if self.p.checksubmit:
            self.check_submitted()

        # Iterate once over all elements of the pending queue
        for i in range(len(self.pending)):

            order = self.pending.popleft()

            if order.expire():
                self.notify(order)
                continue

            self._try_exec(order)

            if order.alive():
                self.pending.append(order)

        # Operations have been executed ... adjust cash end of bar
        for data, pos in self.positions.items():
            # futures change cash every bar
            if pos:
                comminfo = self.getcommissioninfo(data)
                self.cash += comminfo.cashadjust(pos.size,
                                                 pos.adjbase,
                                                 data.close[0])
                # record the last adjustment price
                pos.adjbase = data.close[0]

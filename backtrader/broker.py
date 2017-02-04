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

from backtrader.comminfo import CommInfoBase
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass

from . import fillers as fillers
from . import fillers as filler


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
        '''Retrieves the ``CommissionInfo`` scheme associated with the given
        ``data``'''
        if data._name in self.comminfo:
            return self.comminfo[data._name]

        return self.comminfo[None]

    def setcommission(self,
                      commission=0.0, margin=None, mult=1.0,
                      commtype=None, percabs=True, stocklike=False,
                      interest=0.0, interest_long=False, leverage=1.0,
                      automargin=False,
                      name=None):

        '''This method sets a `` CommissionInfo`` object for assets managed in
        the broker with the parameters. Consult the reference for
        ``CommInfoBase``

        If name is ``None``, this will be the default for assets for which no
        other ``CommissionInfo`` scheme can be found
        '''

        comm = CommInfoBase(commission=commission, margin=margin, mult=mult,
                            commtype=commtype, stocklike=stocklike,
                            percabs=percabs,
                            interest=interest, interest_long=interest_long,
                            leverage=leverage, automargin=automargin)
        self.comminfo[name] = comm

    def addcommissioninfo(self, comminfo, name=None):
        '''Adds a ``CommissionInfo`` object that will be the default for all assets if
        ``name`` is ``None``'''
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

# __all__ = ['BrokerBase', 'fillers', 'filler']

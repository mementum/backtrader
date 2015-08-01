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

import six

from .metabase import MetaParams
from .lineiterator import LineIterator, LineObserverBase, StrategyBase


class MetaLineObserver(LineObserverBase.__class__):

    def dopreinit(cls, _obj, *args, **kwargs):
        # Make a copy of the owner datas .. this ensures the clock up the chain
        # will be taken from the datas - slice or object reference ...
        _obj.datas = _obj._owner.datas

        _obj, args, kwargs = \
            super(MetaLineObserver, cls).dopreinit(_obj, *args, **kwargs)

        return _obj, args, kwargs


class LineObserver(six.with_metaclass(MetaLineObserver, LineObserverBase)):
    _OwnerCls = StrategyBase
    _ltype = LineIterator.ObsType

    extralines = 1


# class ObserverPot(six.with_metaclass(MetaParams, object)):
class ObserverPot(LineObserver):
    plotinfo = dict(plot=False, plotskip=True)

    def __init__(self, *args, **kwargs):
        self.pot = dict()
        for data in self.datas:
            self.pot[data] = self._ObserverCls(
                data, *args, plot=self.plotinfo.plot, **kwargs)

    def __getitem__(self, key):
        return self.pot[key]

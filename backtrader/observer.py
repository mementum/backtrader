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


from .lineiterator import LineIterator, ObserverBase, StrategyBase
from backtrader.utils.py3 import with_metaclass


class MetaObserver(ObserverBase.__class__):
    '''Observer metaclass 的基类，用于完成 observer 初始化挂接。'''

    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaObserver, cls).donew(*args, **kwargs)
        _obj._analyzers = list()  # 保存子 analyzer

        return _obj, args, kwargs  # 返回实例化对象和参数

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaObserver, cls).dopreinit(_obj, *args, **kwargs)

        if _obj._stclock:  # strategy-wide observer 使用 strategy clock
            _obj._clock = _obj._owner

        return _obj, args, kwargs


class Observer(with_metaclass(MetaObserver, ObserverBase)):
    '''Observer 的基类，用于在 strategy 运行时观察并记录状态。'''

    _stclock = False

    _OwnerCls = StrategyBase
    _ltype = LineIterator.ObsType

    csv = True

    plotinfo = dict(plot=False, subplot=True)

    # Observer 理想情况下应始终观察，因此 prenext 调用 next。
    # 子类可以覆盖该行为。
    def prenext(self):
        self.next()

    def _register_analyzer(self, analyzer):
        self._analyzers.append(analyzer)

    def _start(self):
        self.start()

    def start(self):
        pass

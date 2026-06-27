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


from datetime import datetime

import backtrader as bt
from backtrader.utils.py3 import range


class MetaChainer(bt.DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，随后进行初始化注册。'''
        # 初始化类对象
        super(MetaChainer, cls).__init__(name, bases, dct)

    def donew(cls, *args, **kwargs):
        '''拦截构造过程，从第一个 data 复制 timeframe/compression。'''
        # 创建对象并设置参数
        _obj, args, kwargs = super(MetaChainer, cls).donew(*args, **kwargs)

        if args:
            _obj.p.timeframe = args[0]._timeframe
            _obj.p.compression = args[0]._compression

        return _obj, args, kwargs


class Chainer(bt.with_metaclass(MetaChainer, bt.DataBase)):
    '''把多个 data feed 按时间顺序串接成一个连续数据源。

    Args:
        *args: 按顺序传入的多个 data feed。前一个耗尽后，会切到后一个；已经输出过
            的时间不会重复输出。

    Returns:
        Chainer: 可加入 Cerebro 的串接数据源实例。

    ---
    交互界面使用示范:

    >>> data = Chainer()
    >>> data._args
    ()
    '''

    def islive(self):
        '''返回 ``True``，通知 ``Cerebro`` 关闭 preload 和 runonce。'''
        return True

    def __init__(self, *args):
        self._args = args

    def start(self):
        super(Chainer, self).start()
        for d in self._args:
            d.setenvironment(self._env)
            d._start()

        # 把引用放到单独列表中，便于按顺序 pop
        self._ds = list(self._args)
        self._d = self._ds.pop(0) if self._ds else None
        self._lastdt = datetime.min

    def stop(self):
        super(Chainer, self).stop()
        for d in self._args:
            d.stop()

    def get_notifications(self):
        return [] if self._d is None else self._d.get_notifications()

    def _gettz(self):
        '''供子类覆写，用于自动计算 timezone。'''
        if self._args:
            return self._args[0]._gettz()
        return bt.utils.date.Localizer(self.p.tz)

    def _load(self):
        while self._d is not None:
            if not self._d.next():  # 当前数据源已经没有值
                self._d = self._ds.pop(0) if self._ds else None
                continue

            # 不能输出早于或等于已输出时间的 bar
            dt = self._d.datetime.datetime()
            if dt <= self._lastdt:
                continue

            self._lastdt = dt

            for i in range(self._d.size()):
                self.lines[i][0] = self._d.lines[i][0]

            return True

        # 退出循环表示 self._d 为 None，没有 data feed 可继续返回
        return False

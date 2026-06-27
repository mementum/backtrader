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


class MetaRollOver(bt.DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，随后进行初始化注册。'''
        # 初始化类对象
        super(MetaRollOver, cls).__init__(name, bases, dct)

    def donew(cls, *args, **kwargs):
        '''拦截构造过程，从第一个 data 复制 timeframe/compression。'''
        # 创建对象并设置参数
        _obj, args, kwargs = super(MetaRollOver, cls).donew(*args, **kwargs)

        if args:
            _obj.p.timeframe = args[0]._timeframe
            _obj.p.compression = args[0]._compression

        return _obj, args, kwargs


class RollOver(bt.with_metaclass(MetaRollOver, bt.DataBase)):
    '''在满足条件时切换到下一份期货合约的数据源。

    Args:
        *args: 按合约顺序传入的多个 data feed，当前合约满足切换规则后会切到下一个。
        checkdate: 可调用对象，签名为 ``checkdate(dt, d)``。``dt`` 是当前 active
            data 的 ``datetime.datetime``，``d`` 是当前 active data feed。只要返回
            ``True``，就允许进入切换判断窗口。
        checkcondition: 可调用对象，签名为 ``checkcondition(d0, d1)``。只有
            ``checkdate`` 返回 ``True`` 时才会调用。``d0`` 是当前 active data，
            ``d1`` 是下一份到期合约 data。返回 ``True`` 时执行 roll-over。

    Returns:
        RollOver: 可加入 Cerebro 的连续期货 roll-over 数据源实例。

    ---
    交互界面使用示范:

    >>> data = RollOver(checkdate=lambda dt, d: False)
    >>> data.p.checkdate is not None
    True
    '''

    params = (
        # ('rolls', []),  # 待 roll-over 的期货数据数组
        ('checkdate', None),  # callable
        ('checkcondition', None),  # callable
    )

    def islive(self):
        '''返回 ``True``，通知 ``Cerebro`` 关闭 preload 和 runonce。'''
        return True

    def __init__(self, *args):
        self._rolls = args

    def start(self):
        super(RollOver, self).start()
        for d in self._rolls:
            d.setenvironment(self._env)
            d._start()

        # 把引用放到单独列表中，便于按顺序 pop
        self._ds = list(self._rolls)
        self._d = self._ds.pop(0) if self._ds else None
        self._dexp = None
        self._dts = [datetime.min for xx in self._ds]

    def stop(self):
        super(RollOver, self).stop()
        for d in self._rolls:
            d.stop()

    def _gettz(self):
        '''供子类覆写，用于自动计算 timezone。'''
        if self._rolls:
            return self._rolls[0]._gettz()
        return bt.utils.date.Localizer(self.p.tz)

    def _checkdate(self, dt, d):
        if self.p.checkdate is not None:
            return self.p.checkdate(dt, d)

        return False

    def _checkcondition(self, d0, d1):
        if self.p.checkcondition is not None:
            return self.p.checkcondition(d0, d1)

        return True

    def _load(self):
        while self._d is not None:
            _next = self._d.next()
            if _next is None:  # 暂时没有值，后续还会有
                continue
            if _next is False:  # 当前数据源已经没有值
                if self._ds:
                    self._d = self._ds.pop(0)
                    self._dts.pop(0)
                else:
                    self._d = None
                continue

            dt0 = self._d.datetime.datetime()  # 当前 active data 的时间

            # 使用 dt0 同步其他 data
            for i, d_dt in enumerate(zip(self._ds, self._dts)):
                d, dt = d_dt
                while dt < dt0:
                    if d.next() is None:
                        continue
                    self._dts[i] = dt = d.datetime.datetime()

            # 推进已经过期的合约，直到追上当前时间或耗尽
            while self._dexp is not None:
                if not self._dexp.next():
                    self._dexp = None
                    break

                if self._dexp.datetime.datetime() < dt0:
                    continue

            if self._dexp is None and self._checkdate(dt0, self._d):
                # 日期规则已满足；只有还有下一份 data 时才检查其他条件
                if self._ds and self._checkcondition(self._d, self._ds[0]):
                    # 可以切换到下一份 data
                    self._dexp = self._d
                    self._d = self._ds.pop(0)
                    self._dts.pop(0)

            # 填充当前 line，并返回已加载
            self.lines.datetime[0] = self._d.lines.datetime[0]
            self.lines.open[0] = self._d.lines.open[0]
            self.lines.high[0] = self._d.lines.high[0]
            self.lines.low[0] = self._d.lines.low[0]
            self.lines.close[0] = self._d.lines.close[0]
            self.lines.volume[0] = self._d.lines.volume[0]
            self.lines.openinterest[0] = self._d.lines.openinterest[0]
            return True

        # 退出循环表示 self._d 为 None，没有 data feed 可继续返回
        return False

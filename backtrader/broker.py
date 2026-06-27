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

from backtrader.comminfo import CommInfoBase
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass

from . import fillers as fillers
from . import fillers as filler


class MetaBroker(MetaParams):
    def __init__(cls, name, bases, dct):
        '''
        类已经创建完成；按需补齐缺失方法。
        '''
        # 初始化类
        super(MetaBroker, cls).__init__(name, bases, dct)
        translations = {
            'get_cash': 'getcash',
            'get_value': 'getvalue',
        }

        for attr, trans in translations.items():
            if not hasattr(cls, attr):
                setattr(cls, name, getattr(cls, trans))


class BrokerBase(with_metaclass(MetaBroker, object)):
    '''Broker 的基类，用于定义 broker 实现需要提供的基础接口。

    该类负责保存 commission scheme，并定义 cash/value、position、submit、
    cancel、buy、sell 等 broker 行为的抽象接口。具体 broker 子类需要覆盖
    未实现的方法。
    '''

    params = (
        ('commission', CommInfoBase(percabs=True)),
    )

    def __init__(self):
        self.comminfo = dict()
        self.init()

    def init(self):
        # 从 init 和 start 中调用
        if None not in self.comminfo:
            self.comminfo = dict({None: self.p.commission})

    def start(self):
        self.init()

    def stop(self):
        pass

    def add_order_history(self, orders, notify=False):
        '''添加 order history。

        Args:
            orders: order history 数据。
            notify (bool): 是否发送通知。

        详情参见 cerebro。
        '''
        raise NotImplementedError

    def set_fund_history(self, fund):
        '''添加 fund history。

        Args:
            fund: fund history 数据。

        详情参见 cerebro。
        '''
        raise NotImplementedError

    def getcommissioninfo(self, data):
        '''获取与给定 ``data`` 关联的 ``CommissionInfo`` scheme。

        Args:
            data: 需要查询 commission scheme 的 data。

        Returns:
            CommInfoBase: 与 data 关联的 commission scheme；如果没有 data 专属
            scheme，则返回默认 scheme。
        '''
        if data._name in self.comminfo:
            return self.comminfo[data._name]

        return self.comminfo[None]

    def setcommission(self,
                      commission=0.0, margin=None, mult=1.0,
                      commtype=None, percabs=True, stocklike=False,
                      interest=0.0, interest_long=False, leverage=1.0,
                      automargin=False,
                      name=None):

        '''使用参数为 broker 管理的资产设置 ``CommissionInfo`` 对象。

        Args:
            commission (float): commission 数值。
            margin: margin 设置。
            mult (float): asset value/profit 乘数。
            commtype: commission 类型。
            percabs (bool): 百分比 commission 是否按 0.XX 理解。
            stocklike (bool): 是否按 stock-like 行为处理。
            interest (float): 年化 credit interest。
            interest_long (bool): long position 是否也收取 interest。
            leverage (float): leverage 值。
            automargin: 自动 margin 规则。
            name: data 名称。如果为 ``None``，则作为没有专属 scheme 的资产的
                默认 scheme。

        详情参见 ``CommInfoBase``。
        '''

        comm = CommInfoBase(commission=commission, margin=margin, mult=mult,
                            commtype=commtype, stocklike=stocklike,
                            percabs=percabs,
                            interest=interest, interest_long=interest_long,
                            leverage=leverage, automargin=automargin)
        self.comminfo[name] = comm

    def addcommissioninfo(self, comminfo, name=None):
        '''添加 ``CommissionInfo`` 对象。

        Args:
            comminfo: 要添加的 commission info 对象。
            name: data 名称。如果为 ``None``，则该对象作为所有资产的默认
                commission info。
        '''
        self.comminfo[name] = comminfo

    def getcash(self):
        raise NotImplementedError

    def getvalue(self, datas=None):
        raise NotImplementedError

    def get_fundshares(self):
        '''返回 fund-like 模式下当前 share 数量。

        Returns:
            float: 当前 fund shares。抽象模式只有 1 份。
        '''
        return 1.0  # 抽象模式只有 1 share

    fundshares = property(get_fundshares)

    def get_fundvalue(self):
        return self.getvalue()

    fundvalue = property(get_fundvalue)

    def set_fundmode(self, fundmode, fundstartval=None):
        '''设置实际 fundmode。

        Args:
            fundmode (bool): 是否启用 fundmode。
            fundstartval: 可选初始 fund value。如果不是 ``None``，子类可使用它。
        '''
        pass  # 不执行任何操作，不是所有 broker 都支持该功能

    def get_fundmode(self):
        '''返回实际 fundmode。

        Returns:
            bool: 当前是否启用 fundmode。
        '''
        return False

    fundmode = property(get_fundmode, set_fundmode)

    def getposition(self, data):
        raise NotImplementedError

    def submit(self, order):
        raise NotImplementedError

    def cancel(self, order):
        raise NotImplementedError

    def buy(self, owner, data, size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            **kwargs):

        raise NotImplementedError

    def sell(self, owner, data, size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             **kwargs):

        raise NotImplementedError

    def next(self):
        pass

# __all__ = ['BrokerBase', 'fillers', 'filler']

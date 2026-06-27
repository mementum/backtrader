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

import collections

from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass


class MetaSingleton(MetaParams):
    '''singleton metaclass 的基类，用于让使用该 metaclass 的类保持单例。'''

    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


class Store(with_metaclass(MetaSingleton, object)):
    '''Store 的基类，用于统一管理 broker/data 的注册、启动和通知。'''

    _started = False

    params = ()

    def getdata(self, *args, **kwargs):
        '''创建并返回注册的 ``DataCls`` 实例。

        Args:
            *args: 传给 ``DataCls`` 的位置参数。
            **kwargs: 传给 ``DataCls`` 的关键字参数。

        Returns:
            DataCls: 已绑定当前 store 的 data 实例。
        '''
        data = self.DataCls(*args, **kwargs)
        data._store = self
        return data

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''创建并返回注册的 ``BrokerCls`` 实例。

        Args:
            *args: 传给 ``BrokerCls`` 的位置参数。
            **kwargs: 传给 ``BrokerCls`` 的关键字参数。

        Returns:
            BrokerCls: 已绑定当前 store 类的 broker 实例。
        '''
        broker = cls.BrokerCls(*args, **kwargs)
        broker._store = cls
        return broker

    BrokerCls = None  # broker class 会自动注册
    DataCls = None  # data class 会自动注册

    def start(self, data=None, broker=None):
        '''启动 store，并按需关联 data 或 broker。'''
        if not self._started:
            self._started = True
            self.notifs = collections.deque()
            self.datas = list()
            self.broker = None

        if data is not None:
            self._cerebro = self._env = data._env
            self.datas.append(data)

            if self.broker is not None:
                if hasattr(self.broker, 'data_started'):
                    self.broker.data_started(data)

        elif broker is not None:
            self.broker = broker

    def stop(self):
        '''停止 store 的 hook。'''
        pass

    def put_notification(self, msg, *args, **kwargs):
        '''保存一条 store notification。'''
        self.notifs.append((msg, args, kwargs))

    def get_notifications(self):
        '''返回待处理的 store notification。'''
        self.notifs.append(None)  # 放置标记；其它线程仍可能继续 append
        return [x for x in iter(self.notifs.popleft, None)]

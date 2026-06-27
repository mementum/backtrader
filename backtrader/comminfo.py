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

import datetime

from .utils.py3 import with_metaclass
from .metabase import MetaParams


class CommInfoBase(with_metaclass(MetaParams)):
    '''Commission Schemes 的基类，用于描述资产的 commission、margin、leverage
    和 credit interest 计算规则。

    Args:
        commission (float): 基础 commission 数值，可以表示百分比或货币单位。
        mult (float): 用于 asset value/profit 的乘数。
        margin: 打开/持有一次操作所需的货币单位数量。仅当最终 ``_stocklike``
            属性为 ``False`` 时适用。
        automargin: 由 ``get_margin`` 用于自动计算所需 margin/guarantees。
            规则如下:

            - 如果 ``automargin`` 为 ``False``，使用参数 ``margin``
            - 如果 ``automargin < 0``，使用 ``mult * price``
            - 如果 ``automargin > 0``，使用 ``automargin * price``

        commtype: 支持 ``CommInfoBase.COMM_PERC`` 和
            ``CommInfoBase.COMM_FIXED``。``COMM_PERC`` 表示 commission 按
            百分比理解，``COMM_FIXED`` 表示 commission 按货币单位理解。

            ``None`` 是受支持的默认值，用于保持与旧版 ``CommissionInfo`` 对象
            兼容。如果 ``commtype`` 为 ``None``，则:

            - ``margin`` 为 ``None``: 内部 ``_commtype`` 设为 ``COMM_PERC``，
              ``_stocklike`` 设为 ``True``（按股票式百分比运作）
            - ``margin`` 不为 ``None``: 内部 ``_commtype`` 设为
              ``COMM_FIXED``，``_stocklike`` 设为 ``False``（按 futures 式固定
              round-trip commission 运作）

            如果该参数不是 ``None``，则会赋值给内部 ``_commtype`` 属性；参数
            ``stocklike`` 也会同样赋值给内部 ``_stocklike`` 属性。

        stocklike (bool): 表示 instrument 是 Stock-like 还是 Futures-like
            （见上方 ``commtype`` 说明）。
        percabs (bool): 当 ``commtype`` 为 ``COMM_PERC`` 时，表示参数
            ``commission`` 应按 XX% 还是 0.XX 理解。``True`` 表示 0.XX，
            ``False`` 表示 XX%。
        interest (float): 持有 short selling position 时收取的年化 interest。
            主要用于股票 short-selling。公式为
            ``days * price * abs(size) * (interest / 365)``。必须按绝对值指定:
            0.05 表示 5%。
        interest_long (bool): 某些产品（如 ETF）会对 short 和 long position
            都收取 interest。如果该值为 ``True`` 且 ``interest`` 非零，则两个
            方向都会收取 interest。
        leverage (float): 该 asset 相对于所需 cash 的 leverage。

    Attributes:
        _stocklike: 最终用于 Stock-like/Futures-like 行为的值。
        _commtype: 最终用于 PERC/FIXED commission 行为的值。

    ``_stocklike`` 和 ``_commtype`` 在内部使用，而不是直接使用声明参数，以便
    执行上面描述的旧版 ``CommissionInfo`` 兼容性检查。

    '''

    COMM_PERC, COMM_FIXED = range(2)

    params = (
        ('commission', 0.0), ('mult', 1.0), ('margin', None),
        ('commtype', None),
        ('stocklike', False),
        ('percabs', False),
        ('interest', 0.0),
        ('interest_long', False),
        ('leverage', 1.0),
        ('automargin', False),
    )

    def __init__(self):
        super(CommInfoBase, self).__init__()

        self._stocklike = self.p.stocklike
        self._commtype = self.p.commtype

        # 初始代码块检查原始 CommissionInfo 的行为：commission scheme
        # (perc/fixed) 由参数 "margin" 的 False/True 判定。如果参数
        # "commtype" 为 None，则模拟该行为；否则使用参数值

        if self._commtype is None:  # 使用原始 CommissionInfo 行为
            if self.p.margin:
                self._stocklike = False
                self._commtype = self.COMM_FIXED
            else:
                self._stocklike = True
                self._commtype = self.COMM_PERC

        if not self._stocklike and not self.p.margin:
            self.p.margin = 1.0  # 避免 None/0

        if self._commtype == self.COMM_PERC and not self.p.percabs:
            self.p.commission /= 100.0

        self._creditrate = self.p.interest / 365.0

    @property
    def margin(self):
        return self.p.margin

    @property
    def stocklike(self):
        return self._stocklike

    def get_margin(self, price):
        '''返回给定 price 下单个 asset 实际所需的 margin/guarantees。

        Args:
            price (float): 用于计算 margin 的 asset price。

        Returns:
            float: 实际所需 margin。默认实现使用以下策略:

              - 如果 ``automargin`` 为 ``False``，使用参数 ``margin``
              - 如果 ``automargin < 0``，使用 ``mult * price``
              - 如果 ``automargin > 0``，使用 ``automargin * price``
        '''
        if not self.p.automargin:
            return self.p.margin

        elif self.p.automargin < 0:
            return price * self.p.mult

        return price * self.p.automargin  # int/float expected

    def get_leverage(self):

        '''返回该 commission scheme 允许的 leverage。

        Returns:
            float: 当前 leverage。
        '''
        return self.p.leverage

    def getsize(self, price, cash):
        '''返回给定 price 和 cash 下可满足 cash 操作的 size。

        Args:
            price (float): asset price。
            cash (float): 可用 cash。

        Returns:
            int: 可执行 size。
        '''
        if not self._stocklike:
            return int(self.p.leverage * (cash // self.get_margin(price)))

        return int(self.p.leverage * (cash // price))

    def getoperationcost(self, size, price):
        '''返回一次 operation 所需的 cash 数量。

        Args:
            size (int): operation size。
            price (float): operation price。

        Returns:
            float: 所需 cash。
        '''
        if not self._stocklike:
            return abs(size) * self.get_margin(price)

        return abs(size) * price

    def getvaluesize(self, size, price):
        '''返回给定 price 下 size 对应的 value。

        Args:
            size (int): position 或 operation size。
            price (float): asset price。

        Returns:
            float: 对应 value。对 future-like 对象，固定为 ``size * margin``。
        '''
        if not self._stocklike:
            return abs(size) * self.get_margin(price)

        return size * price

    def getvalue(self, position, price):
        '''返回给定 price 下 position 的 value。

        Args:
            position: 带有 ``size`` 和 ``price`` 属性的 position 对象。
            price (float): 当前 asset price。

        Returns:
            float: position value。对 future-like 对象，固定为 ``size * margin``。
        '''
        if not self._stocklike:
            return abs(position.size) * self.get_margin(price)

        size = position.size
        if size >= 0:
            return size * price

        # 对股票来说，short position 会在 price 下跌时更有价值
        value = position.price * size  # original value
        value += (position.price - price) * size  # increased value
        return value

    def _getcommission(self, size, price, pseudoexec):
        '''计算给定 price 下一次 operation 的 commission。

        Args:
            size (int): operation size。
            price (float): operation price。
            pseudoexec (bool): 如果为 ``True``，表示 operation 尚未实际执行。

        Returns:
            float: commission 金额。
        '''
        if self._commtype == self.COMM_PERC:
            return abs(size) * self.p.commission * price

        return abs(size) * self.p.commission

    def getcommission(self, size, price):
        '''计算给定 price 下一次 operation 的 commission。

        Args:
            size (int): operation size。
            price (float): operation price。

        Returns:
            float: commission 金额。
        '''
        return self._getcommission(size, price, pseudoexec=True)

    def confirmexec(self, size, price):
        '''确认实际执行后的 commission。

        Args:
            size (int): executed size。
            price (float): executed price。

        Returns:
            float: 实际执行 commission。
        '''
        return self._getcommission(size, price, pseudoexec=False)

    def profitandloss(self, size, price, newprice):
        '''返回 position 的实际 profit and loss。

        Args:
            size (int): position size。
            price (float): 原始 price。
            newprice (float): 新 price。

        Returns:
            float: profit and loss。
        '''
        return size * (newprice - price) * self.p.mult

    def cashadjust(self, size, price, newprice):
        '''根据 price 差值计算 cash adjustment。

        Args:
            size (int): position size。
            price (float): 原始 price。
            newprice (float): 新 price。

        Returns:
            float: cash adjustment。stock-like 对象返回 ``0.0``。
        '''
        if not self._stocklike:
            return size * (newprice - price) * self.p.mult

        return 0.0

    def get_credit_interest(self, data, pos, dt):
        '''计算 short selling 或特定产品产生的 credit interest。

        Args:
            data: 产生 interest 的 data feed。
            pos: 当前 position，需包含 ``size``、``price`` 和 ``datetime``。
            dt (datetime.datetime): 当前 datetime。

        Returns:
            float: 应计 credit interest。
        '''
        size, price = pos.size, pos.price

        if size > 0 and not self.p.interest_long:
            return 0.0  # long positions 不收费

        dt0 = dt.date()
        dt1 = pos.datetime.date()

        if dt0 <= dt1:
            return 0.0

        return self._get_credit_interest(data, size, price,
                                         (dt0 - dt1).days, dt0, dt1)

    def _get_credit_interest(self, data, size, price, days, dt0, dt1):
        '''
        返回 broker 收取的 credit interest 成本。

        当 ``size > 0`` 时，只有类参数 ``interest_long`` 为 ``True`` 才会调用
        该方法。

        credit interest rate 的计算公式为:

          ``days * price * abs(size) * (interest / 365)``


        Args:
            data: 收取 interest 的 data feed。
            size (int): 当前 position size。> 0 表示 long position，< 0 表示
                short position（该参数不会为 ``0``）。
            price (float): 当前 position price。
            days (int): 距上次 credit 计算经过的天数，即 ``(dt0 - dt1).days``。
            dt0 (datetime.datetime): 当前 datetime。
            dt1 (datetime.datetime): 上次计算的 datetime。

        Returns:
            float: credit interest 成本。

        ``dt0`` 和 ``dt1`` 在默认实现中未使用，只是作为额外输入提供给覆盖方法。
        '''
        return days * self._creditrate * abs(size) * price


class CommissionInfo(CommInfoBase):
    '''实际 Commission Schemes 的基类，用于兼容旧版 commission 行为。

    ``CommInfoBase`` 用于保留 *backtrader* 原始但不完整的支持。新的 commission
    schemes 从该类派生，而该类继承 ``CommInfoBase``。

    ``percabs`` 的默认值也改为 ``True``。

    Args:
        percabs (bool): 当 ``commtype`` 为 COMM_PERC 时，表示参数
            ``commission`` 应按 XX% 还是 0.XX 理解。``True`` 表示 0.XX，
            ``False`` 表示 XX%。

    旧版 ``CommissionInfo`` 将 0.xx 作为百分比输入。

    '''
    params = (
        ('percabs', True),  # Original CommissionInfo took 0.xx for percentages
    )

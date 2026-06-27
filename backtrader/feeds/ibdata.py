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

import backtrader as bt
from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num, num2date
from backtrader.utils.py3 import (integer_types, queue, string_types,
                                  with_metaclass)
from backtrader.metabase import MetaParams
from backtrader.stores import ibstore


class MetaIBData(DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，随后把它注册到对应 store。'''
        # 初始化类对象
        super(MetaIBData, cls).__init__(name, bases, dct)

        # 注册到 store，供 IBStore 找到实际 DataCls
        ibstore.IBStore.DataCls = cls


class IBData(with_metaclass(MetaIBData, DataBase)):
    '''Interactive Brokers 数据源。

    Args:
        dataname: IB contract 描述字符串。支持下列格式：

          - TICKER  # Stock 类型和 SMART 交易所
          - TICKER-STK  # Stock 和 SMART 交易所
          - TICKER-STK-EXCHANGE  # Stock
          - TICKER-STK-EXCHANGE-CURRENCY  # Stock

          - TICKER-CFD  # CFD 和 SMART 交易所
          - TICKER-CFD-EXCHANGE  # CFD
          - TICKER-CDF-EXCHANGE-CURRENCY  # Stock

          - TICKER-IND-EXCHANGE  # 指数
          - TICKER-IND-EXCHANGE-CURRENCY  # 指数

          - TICKER-YYYYMM-EXCHANGE  # 期货
          - TICKER-YYYYMM-EXCHANGE-CURRENCY  # 期货
          - TICKER-YYYYMM-EXCHANGE-CURRENCY-MULT  # 期货
          - TICKER-FUT-EXCHANGE-CURRENCY-YYYYMM-MULT # 期货

          - TICKER-YYYYMM-EXCHANGE-CURRENCY-STRIKE-RIGHT  # FOP
          - TICKER-YYYYMM-EXCHANGE-CURRENCY-STRIKE-RIGHT-MULT  # FOP
          - TICKER-FOP-EXCHANGE-CURRENCY-YYYYMM-STRIKE-RIGHT # FOP
          - TICKER-FOP-EXCHANGE-CURRENCY-YYYYMM-STRIKE-RIGHT-MULT # FOP

          - CUR1.CUR2-CASH-IDEALPRO  # 外汇

          - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-STRIKE-RIGHT  # OPT
          - TICKER-YYYYMMDD-EXCHANGE-CURRENCY-STRIKE-RIGHT-MULT  # OPT
          - TICKER-OPT-EXCHANGE-CURRENCY-YYYYMMDD-STRIKE-RIGHT # OPT
          - TICKER-OPT-EXCHANGE-CURRENCY-YYYYMMDD-STRIKE-RIGHT-MULT # OPT

        sectype: ``dataname`` 未提供 security type 时使用的默认值，默认 ``STK``。
        exchange: ``dataname`` 未提供 exchange 时使用的默认值，默认 ``SMART``。
        currency: ``dataname`` 未提供 currency 时使用的默认值，默认空字符串。
        historical: 为 ``True`` 时，完成首次历史数据下载后停止。会使用标准 data feed
            参数 ``fromdate`` 和 ``todate`` 作为时间范围。若请求范围超过 IB 在当前
            timeframe/compression 下允许的范围，会拆成多次请求。
        what: 历史数据请求类型。``None`` 时按资产类型使用默认值：``CASH`` 使用
            ``'BID'``，其他资产使用 ``'TRADES'``。现金资产也可使用 ``'ASK'``。
        rtbar: 为 ``True`` 时使用 IB 的 ``5 Seconds Realtime bars``；为 ``False``
            时使用基于 tick 的 ``RTVolume``。``CASH`` 资产始终使用 ``RTVolume``。
        useRTH: 历史数据是否仅下载 Regular Trading Hours。
        qcheck: 没有收到数据时的唤醒间隔（秒），用于给 resample/replay 和 notification
            传播留出处理机会。
        backfill_start: 启动时是否执行 backfill。会在单次请求中尽可能获取最大历史数据。
        backfill: 断线/重连后是否执行 backfill。会按缺口时长下载尽量小的数据范围。
        backfill_from: 额外的初始 backfill 数据源。该数据源耗尽后，如有需要，再从 IB
            拉取 backfill 数据。
        latethrough: resample/replay 后，如果 tick 晚于已输出的 bar，是否仍允许其通过。
        tradename: 与 ``dataname`` 不同的交易标的名称，常用于 CFD 等“报价资产”和
            “交易资产”不同的场景。

    Returns:
        IBData: 可加入 Cerebro 的 Interactive Brokers 数据源实例。

    默认参数允许像 ``TICKER`` 这样的简写形式，此时会自动套用 ``sectype='STK'`` 和
    ``exchange='SMART'``。例如 ``AAPL-STK-SMART-USD`` 是完整写法，也可以写成
    ``IBData(dataname='AAPL', currency='USD')``。

    ---
    交互界面使用示范:

    >>> data = IBData(dataname='AAPL', currency='USD')  # doctest: +SKIP
    >>> data.p.currency  # doctest: +SKIP
    'USD'
    '''
    params = (
        ('sectype', 'STK'),  # 行业常用默认值
        ('exchange', 'SMART'),  # 行业常用默认值
        ('currency', ''),
        ('rtbar', False),  # 使用 RealTime 5 秒 bar
        ('historical', False),  # 仅下载历史数据
        ('what', None),  # 历史数据请求类型
        ('useRTH', False),  # 历史数据仅下载 Regular Trading Hours
        ('qcheck', 0.5),  # 检查事件的超时时间（秒，float）
        ('backfill_start', True),  # 启动时执行 backfill
        ('backfill', True),  # 重连时执行 backfill
        ('backfill_from', None),  # 用于 backfill 的额外数据源
        ('latethrough', False),  # 允许延迟样本通过
        ('tradename', None),  # 使用不同资产作为下单目标
    )

    _store = ibstore.IBStore

    # 实时 bar 支持的最小周期
    RTBAR_MINSIZE = (TimeFrame.Seconds, 5)

    # _load 中有限状态机的状态
    _ST_FROM, _ST_START, _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(5)

    def _timeoffset(self):
        return self.ib.timeoffset()

    def _gettz(self):
        # 如果用户没有提供 timezone 对象，但 contractdetails 中可以找到 timezone，
        # 就尝试通过 pytz 获取；pytz 可能不存在。

        # TWS 返回的 timezone 看起来是 pytz 能理解的缩写，但 TWS 可能返回的完整列表
        # 没有文档保证，某些缩写可能失败
        tzstr = isinstance(self.p.tz, string_types)
        if self.p.tz is not None and not tzstr:
            return bt.utils.date.Localizer(self.p.tz)

        if self.contractdetails is None:
            return None  # 无法继续处理

        try:
            import pytz  # 保持局部导入
        except ImportError:
            return None  # 无法继续处理

        tzs = self.p.tz if tzstr else self.contractdetails.m_timeZoneId

        if tzs == 'CST':  # TWS 返回值，与 pytz 不兼容，需要修正
            tzs = 'CST6CDT'

        try:
            tz = pytz.timezone(tzs)
        except pytz.UnknownTimeZoneError:
            return None  # 无法继续处理

        # contractdetails 存在，导入成功，timezone 已找到，直接返回
        return tz

    def islive(self):
        '''返回 ``True``，通知 ``Cerebro`` 关闭 preload 和 runonce。'''
        return not self.p.historical

    def __init__(self, **kwargs):
        self.ib = self._store(**kwargs)
        self.precontract = self.parsecontract(self.p.dataname)
        self.pretradecontract = self.parsecontract(self.p.tradename)

    def setenvironment(self, env):
        '''接收 Cerebro 环境，并把它传给所属 store。'''
        super(IBData, self).setenvironment(env)
        env.addstore(self.ib)

    def parsecontract(self, dataname):
        '''解析 dataname，并生成默认 contract。'''
        # 为 ticker 字符串中的可选 token 设置默认值
        if dataname is None:
            return None

        exch = self.p.exchange
        curr = self.p.currency
        expiry = ''
        strike = 0.0
        right = ''
        mult = ''

        # 拆分 ticker 字符串
        tokens = iter(dataname.split('-'))

        # symbol 和 security type 是必需字段
        symbol = next(tokens)
        try:
            sectype = next(tokens)
        except StopIteration:
            sectype = self.p.sectype

        # security type 位置也可能是到期日
        if sectype.isdigit():
            expiry = sectype  # 保存到期日

            if len(sectype) == 6:  # YYYYMM
                sectype = 'FUT'
            else:  # 视为 OPTIONS - YYYYMMDD
                sectype = 'OPT'

        if sectype == 'CASH':  # Forex 需要拆出 currency
            symbol, curr = symbol.split('.')

        # 检查是否提供了可选 token
        try:
            exch = next(tokens)  # 异常时保持默认值
            curr = next(tokens)  # 异常时保持默认值

            if sectype == 'FUT':
                if not expiry:
                    expiry = next(tokens)
                mult = next(tokens)

                # 尝试判断是否为 FOP - Futures on OPTIONS
                right = next(tokens)
                # 能走到这里说明是 FOP，而不是 FUT
                sectype = 'FOP'
                strike, mult = float(mult), ''  # 转给 strike，并清空 mult

                mult = next(tokens)  # 再尝试读取 mult

            elif sectype == 'OPT':
                if not expiry:
                    expiry = next(tokens)
                strike = float(next(tokens))  # 异常时保持默认值
                right = next(tokens)  # 异常时保持默认值

                mult = next(tokens)  # 即使不存在也无妨

        except StopIteration:
            pass

        # 创建初始 contract
        precon = self.ib.makecontract(
            symbol=symbol, sectype=sectype, exch=exch, curr=curr,
            expiry=expiry, strike=strike, right=right, mult=mult)

        return precon

    def start(self):
        '''启动 IB 连接，并在存在时获取真实 contract 和 contractdetails。'''
        super(IBData, self).start()
        # 启动 store，并获取后续等待的数据队列
        self.qlive = self.ib.start(data=self)
        self.qhist = None

        self._usertvol = not self.p.rtbar
        tfcomp = (self._timeframe, self._compression)
        if tfcomp < self.RTBAR_MINSIZE:
            # 请求的 timeframe/compression 不受 rtbar 支持
            self._usertvol = True

        self.contract = None
        self.contractdetails = None
        self.tradecontract = None
        self.tradecontractdetails = None

        if self.p.backfill_from is not None:
            self._state = self._ST_FROM
            self.p.backfill_from.setenvironment(self._env)
            self.p.backfill_from._start()
        else:
            self._state = self._ST_START  # _load 的初始状态
        self._statelivereconn = False  # 是否在 live 状态下重连
        self._subcription_valid = False  # 订阅状态
        self._storedmsg = dict()  # 保存待处理的 live 消息（键为 None）

        if not self.ib.connected():
            return

        self.put_notification(self.CONNECTED)
        # 通过真实 conId（contractId）获取真实 contract details
        cds = self.ib.getContractDetails(self.precontract, maxcount=1)
        if cds is not None:
            cdetails = cds[0]
            self.contract = cdetails.contractDetails.m_summary
            self.contractdetails = cdetails.contractDetails
        else:
            # 找不到 contract，或匹配到多个
            self.put_notification(self.DISCONNECTED)
            return

        if self.pretradecontract is None:
            # 没有不同的交易资产，默认使用标准资产
            self.tradecontract = self.contract
            self.tradecontractdetails = self.contractdetails
        else:
            # 交易目标资产不同（某些 CDS 产品常见），使用另一套 details
            cds = self.ib.getContractDetails(self.pretradecontract, maxcount=1)
            if cds is not None:
                cdetails = cds[0]
                self.tradecontract = cdetails.contractDetails.m_summary
                self.tradecontractdetails = cdetails.contractDetails
            else:
                # 找不到 contract，或匹配到多个
                self.put_notification(self.DISCONNECTED)
                return

        if self._state == self._ST_START:
            self._start_finish()  # 完成初始化
            self._st_start()

    def stop(self):
        '''停止数据源，并通知 store 停止。'''
        super(IBData, self).stop()
        self.ib.stop()

    def reqdata(self):
        '''请求实时数据，并根据资产类型和 rtbar 参数选择订阅方式。'''
        if self.contract is None or self._subcription_valid:
            return

        if self._usertvol:
            self.qlive = self.ib.reqMktData(self.contract, self.p.what)
        else:
            self.qlive = self.ib.reqRealTimeBars(self.contract)

        self._subcription_valid = True
        return self.qlive

    def canceldata(self):
        '''取消 Market Data 订阅，并根据资产类型和 rtbar 参数选择取消方式。'''
        if self.contract is None:
            return

        if self._usertvol:
            self.ib.cancelMktData(self.qlive)
        else:
            self.ib.cancelRealTimeBars(self.qlive)

    def haslivedata(self):
        return bool(self._storedmsg or self.qlive)

    def _load(self):
        if self.contract is None or self._state == self._ST_OVER:
            return False  # 无法继续处理

        while True:
            if self._state == self._ST_LIVE:
                try:
                    msg = (self._storedmsg.pop(None, None) or
                           self.qlive.get(timeout=self._qcheck))
                except queue.Empty:
                    if True:
                        return None

                # 这段代码在进一步检查前保持无效
                    if not self._statelivereconn:
                        return None  # 表示超时

                    # 等待数据但没有收到，临时补到当前时间
                    dtend = self.num2date(date2num(datetime.datetime.utcnow()))
                    dtbegin = None
                    if len(self) > 1:
                        dtbegin = self.num2date(self.datetime[-1])

                    self.qhist = self.ib.reqHistoricalDataEx(
                        contract=self.contract,
                        enddate=dtend, begindate=dtbegin,
                        timeframe=self._timeframe,
                        compression=self._compression,
                        what=self.p.what, useRTH=self.p.useRTH, tz=self._tz,
                        sessionend=self.p.sessionend)

                    if self._laststatus != self.DELAYED:
                        self.put_notification(self.DELAYED)

                    self._state = self._ST_HISTORBACK

                    self._statelivereconn = False
                    continue  # 重新进入循环并命中 st_historback

                if msg is None:  # historical/backfill 期间连接断开
                    self._subcription_valid = False
                    self.put_notification(self.CONNBROKEN)
                    # 尝试重连
                    if not self.ib.reconnect(resub=True):
                        self.put_notification(self.DISCONNECTED)
                        return False  # 失败

                    self._statelivereconn = self.p.backfill
                    continue

                if msg == -354:
                    self.put_notification(self.NOTSUBSCRIBED)
                    return False

                elif msg == -1100:  # 连接断开
                    # 等待消息后再执行 backfill
                    # self._state = self._ST_DISCONN
                    self._subcription_valid = False
                    self._statelivereconn = self.p.backfill
                    continue

                elif msg == -1102:  # 连接恢复，tickerId 保持
                    # 消息可能重复
                    if not self._statelivereconn:
                        self._statelivereconn = self.p.backfill
                    continue

                elif msg == -1101:  # 连接恢复，tickerId 丢失
                    # 消息可能重复
                    self._subcription_valid = False
                    if not self._statelivereconn:
                        self._statelivereconn = self.p.backfill
                        self.reqdata()  # 重新订阅
                    continue

                elif msg == -10225:  # 发生 Bust event，当前订阅失效
                    self._subcription_valid = False
                    if not self._statelivereconn:
                        self._statelivereconn = self.p.backfill
                        self.reqdata()  # 重新订阅
                    continue

                elif isinstance(msg, integer_types):
                    # 历史数据阶段收到意外 notification，跳过它
                    # 可能是“尚未处理的未连接状态”
                    self.put_notification(self.UNKNOWN, msg)
                    continue

                # 按预期返回类型处理消息
                if not self._statelivereconn:
                    if self._laststatus != self.LIVE:
                        if self.qlive.qsize() <= 1:  # live 队列很短
                            self.put_notification(self.LIVE)

                    if self._usertvol:
                        ret = self._load_rtvolume(msg)
                    else:
                        ret = self._load_rtbar(msg)
                    if ret:
                        return True

                    # 当前消息无法形成 bar，继续取下一条
                    continue

                # 进入重连处理流程，尝试 backfill
                self._storedmsg[None] = msg  # 保存当前消息

                # 否则执行 backfill
                if self._laststatus != self.DELAYED:
                    self.put_notification(self.DELAYED)

                dtend = None
                if len(self) > 1:
                    # len == 1 表示第一次转发
                    # 获取类似 msg.datetime 的 UTC 风格起始时间
                    dtbegin = num2date(self.datetime[-1])
                elif self.fromdate > float('-inf'):
                    dtbegin = num2date(self.fromdate)
                else:  # 1st bar and no begin set
                    # 传 None 表示单次请求尽可能获取最大范围
                    dtbegin = None

                dtend = msg.datetime if self._usertvol else msg.time

                self.qhist = self.ib.reqHistoricalDataEx(
                    contract=self.contract, enddate=dtend, begindate=dtbegin,
                    timeframe=self._timeframe, compression=self._compression,
                    what=self.p.what, useRTH=self.p.useRTH, tz=self._tz,
                    sessionend=self.p.sessionend)

                self._state = self._ST_HISTORBACK
                self._statelivereconn = False  # 不再处于 live 重连状态
                continue

            elif self._state == self._ST_HISTORBACK:
                msg = self.qhist.get()
                if msg is None:  # historical/backfill 期间连接断开
                    # 未处理该情况，直接退出
                    self._subcription_valid = False
                    self.put_notification(self.DISCONNECTED)
                    return False  # 错误处理取消了队列

                elif msg == -354:  # 未订阅数据
                    self._subcription_valid = False
                    self.put_notification(self.NOTSUBSCRIBED)
                    return False

                elif msg == -420:  # 没有数据权限
                    self._subcription_valid = False
                    self.put_notification(self.NOTSUBSCRIBED)
                    return False

                elif isinstance(msg, integer_types):
                    # 历史数据阶段收到意外 notification，跳过它
                    # 可能是“尚未处理的未连接状态”
                    self.put_notification(self.UNKNOWN, msg)
                    continue

                if msg.date is not None:
                    if self._load_rtbar(msg, hist=True):
                        return True  # 加载成功

                    # 日期来自重叠的历史数据请求
                    continue

                # 历史数据结束
                if self.p.historical:  # 仅历史模式
                    self.put_notification(self.DISCONNECTED)
                    return False  # 历史数据结束

                # 还需要进入 live 模式
                self._state = self._ST_LIVE
                continue

            elif self._state == self._ST_FROM:
                if not self.p.backfill_from.next():
                    # 额外 backfill 数据源已经耗尽
                    self._state = self._ST_START
                    continue

                # 复制同名 line
                for alias in self.lines.getlinealiases():
                    lsrc = getattr(self.p.backfill_from.lines, alias)
                    ldst = getattr(self.lines, alias)

                    ldst[0] = lsrc[0]

                return True

            elif self._state == self._ST_START:
                if not self._st_start():
                    return False

    def _st_start(self):
        if self.p.historical:
            self.put_notification(self.DELAYED)
            dtend = None
            if self.todate < float('inf'):
                dtend = num2date(self.todate)

            dtbegin = None
            if self.fromdate > float('-inf'):
                dtbegin = num2date(self.fromdate)

            self.qhist = self.ib.reqHistoricalDataEx(
                contract=self.contract, enddate=dtend, begindate=dtbegin,
                timeframe=self._timeframe, compression=self._compression,
                what=self.p.what, useRTH=self.p.useRTH, tz=self._tz,
                sessionend=self.p.sessionend)

            self._state = self._ST_HISTORBACK
            return True  # 前面继续

        # 请求 live 数据
        if not self.ib.reconnect(resub=True):
            self.put_notification(self.DISCONNECTED)
            self._state = self._ST_OVER
            return False  # 失败

        self._statelivereconn = self.p.backfill_start
        if self.p.backfill_start:
            self.put_notification(self.DELAYED)

        self._state = self._ST_LIVE
        return True  # 前面没有返回时，隐式继续

    def _load_rtbar(self, rtbar, hist=False):
        # 完整的 5 秒 bar 由实时 tick 聚合而来，包含 open/high/low/close/volume
        # 历史数据包含相同字段，但 datetime 使用 'date' 而不是 'time'
        dt = date2num(rtbar.time if not hist else rtbar.date)
        if dt < self.lines.datetime[-1] and not self.p.latethrough:
            return False  # 不能输出早于已输出时间的 bar

        self.lines.datetime[0] = dt
        # 把 tick 写入 bar
        self.lines.open[0] = rtbar.open
        self.lines.high[0] = rtbar.high
        self.lines.low[0] = rtbar.low
        self.lines.close[0] = rtbar.close
        self.lines.volume[0] = rtbar.volume
        self.lines.openinterest[0] = 0

        return True

    def _load_rtvolume(self, rtvol):
        # 单个 tick 会用于整组价格字段；理想情况下它包含 open/high/low/close/volume
        # 转换 datetime
        dt = date2num(rtvol.datetime)
        if dt < self.lines.datetime[-1] and not self.p.latethrough:
            return False  # 不能输出早于已输出时间的 bar

        self.lines.datetime[0] = dt

        # 把 tick 写入 bar
        tick = rtvol.price
        self.lines.open[0] = tick
        self.lines.high[0] = tick
        self.lines.low[0] = tick
        self.lines.close[0] = tick
        self.lines.volume[0] = rtvol.size
        self.lines.openinterest[0] = 0

        return True

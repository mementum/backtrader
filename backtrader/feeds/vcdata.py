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


from datetime import datetime, timedelta, tzinfo

import backtrader as bt
from backtrader import TimeFrame, date2num, num2date
from backtrader.feed import DataBase
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import (integer_types, queue, string_types,
                                  with_metaclass)

from backtrader.stores import vcstore


class MetaVCData(DataBase.__class__):
    def __init__(cls, name, bases, dct):
        '''类已经创建完成，随后把它注册到对应 store。'''
        # 初始化类对象
        super(MetaVCData, cls).__init__(name, bases, dct)

        # 注册到 store，供 VCStore 找到实际 DataCls
        vcstore.VCStore.DataCls = cls


class VCData(with_metaclass(MetaVCData, DataBase)):
    '''VisualChart 数据源。

    Args:
        dataname: VisualChart symbol 名称。
        qcheck: resample/replay 场景下的默认唤醒超时时间，用于检查当前 bar 是否已经
            可以交付。只有插入 resampling/replaying filter 时才使用。
        historical: 若没有提供基类参数 ``todate``，设置为 ``True`` 会强制只下载历史数据；
            如果提供了 ``todate``，也会达到相同效果。
        millisecond: VisualChart 构造的 bar 时间可能形如 ``HH:MM:59.999000``。
            为 ``True`` 时增加 1 毫秒，使其看起来像下一分钟的 ``00.000000``。
        tradename: 连续期货适合跟踪数据但不能交易；可用该参数指定当前可交易期货作为
            交易资产。
        usetimezones: 是否尝试导入 ``pytz`` 并使用 timezone。多数市场可通过
            VisualChart 的 time offset 转为市场时间；部分特殊市场（如 ``096``）需要
            内部补偿和 timezone 支持。

    Returns:
        VCData: 可加入 Cerebro 的 VisualChart 数据源实例。

    ---
    交互界面使用示范:

    >>> data = VCData(dataname='001ES')  # doctest: +SKIP
    >>> data.p.dataname  # doctest: +SKIP
    '001ES'
    '''
    params = (
        ('qcheck', 0.5),  # 检查事件的超时时间（秒，float）
        ('historical', False),  # 行业常用默认值
        ('millisecond', True),  # 修正时间中缺失的 millisecond
        ('tradename', None),  # 实际交易资产名称
        ('usetimezones', True),  # 找到 pytz timezone 时使用它
    )

    # 保存本地时间到 VC Server 时间戳的偏移
    _TOFFSET = timedelta()

    # _load 中有限状态机的状态
    _ST_START, _ST_FEEDING, _ST_NOTFOUND = range(3)

    # 为兼容 VB/Excel 日期而使用的空日期基准
    NULLDATE = datetime(1899, 12, 30, 0, 0, 0)

    # 用于修正 HH:MM:59.999 时间
    MILLISECOND = timedelta(microseconds=1000)

    # 较长的 ping 超时时间
    PING_TIMEOUT = 25.0

    # 不同交易所对应的 timezone
    _TZS = {
        'Europe/London': ('011', '024', '027', '036', '049', '092', '114',
                          # 这些是 global markets
                          '033', '034', '035', '043', '054', '096', '300',),

        'Europe/Berlin': ('005', '006', '008', '012', '013', '014', '015',
                          '017', '019', '025', '029', '030', '037', '038',
                          '052', '053', '060', '061', '072', '073', '074',
                          '075', '080', '093', '094', '097', '111', '112',
                          '113',),

        'Asia/Tokyo': ('031',),
        'Australia/Melbourne': ('032',),
        'America/Argentina/Buenos_Aires': ('044',),
        'America/Sao_Paulo': ('045',),
        'America/Mexico_City': ('046',),
        'America/Santiago': ('047',),

        'US/Eastern': ('003', '004', '009', '010', '028', '040', '041', '055',
                       '090', '095', '099',),
        'US/Central': ('001', '002', '020', '021', '022', '023', '056',),
    }

    # global assets 可能有不同的输出 timezone
    _TZOUT = {
        '096.FTSE': 'Europe/London',
        '096.FTEU3': 'Europe/London',
        '096.MIB30': 'Europe/Berlin',
        '096.SSMI': 'Europe/Berlin',
        '096.HSI': 'Asia/Hong_Kong',
        '096.BVSP': 'America/Sao_Paulo',
        '096.MERVAL': 'America/Argentina/Buenos_Aires',
        '096.DJI': 'US/Eastern',
        '096.IXIC': 'US/Eastern',
        '096.NDX': 'US/Eastern',
    }

    # 这些 global markets 返回的是本地 DST 调整后的时间，与上面的不同，需要再修正
    _EXTRA_TIMEOFFSET = ('096',)

    _TIMEFRAME_BACKFILL = {
        TimeFrame.Ticks: timedelta(days=1),
        TimeFrame.MicroSeconds: timedelta(days=1),
        TimeFrame.Seconds: timedelta(days=1),
        TimeFrame.Minutes: timedelta(days=2),
        TimeFrame.Days: timedelta(days=365),
        TimeFrame.Weeks: timedelta(days=365*2),
        TimeFrame.Months: timedelta(days=365*5),
        TimeFrame.Years: timedelta(days=365*20),
    }

    def _timeoffset(self):
        '''返回本地设备到数据服务器之间计算出的时间偏移。'''
        return self._TOFFSET

    def _gettzinput(self):
        '''返回输入数据应使用的 timezone。'''
        return self._gettz(tzin=True)

    def _gettz(self, tzin=False):
        '''返回数据默认输出 timezone。

        默认返回市场实际交易所在地的 timezone。
        '''
        # 如果用户没有提供 timezone 对象，就按市场代码尝试通过 pytz 获取；
        # pytz 可能不存在。

        # 市场 timezone 表可能无法覆盖全部返回值，某些缩写可能无法被 pytz 识别
        ptz = self.p.tz
        tzstr = isinstance(ptz, string_types)
        if ptz is not None and not tzstr:
            return bt.utils.date.Localizer(ptz)

        if self._state == self._ST_NOTFOUND:
            return None  # 无法继续处理

        if not self.p.usetimezones:
            return None

        try:
            import pytz  # 保持局部导入
        except ImportError:
            return None  # 无法继续处理

        # dataname 010ABCXXXXX -> ABC（第 3、4、5 位）是市场代码
        if tzstr:
            tzs = ptz
        else:
            tzs = None

            if not tzin:
                if self.p.dataname in self._TZOUT:
                    tzs = self._TZOUT[self.p.dataname]

            if tzs is None:
                for mktz, mktcodes in self._TZS.items():
                    if self._mktcode in mktcodes:
                        tzs = mktz
                        break

            if tzs is None:
                return None

            if isinstance(tzs, tzinfo):
                return bt.utils.date.Localizer(tzs)

        if tzs:
            try:
                tz = pytz.timezone(tzs)
            except pytz.UnknownTimeZoneError:
                return None  # 无法继续处理
        else:
            return None

        # 已找到 timezone，直接返回
        return tz

    def islive(self):
        '''返回 ``True``，通知 ``Cerebro`` 关闭 preload 和 runonce。'''
        return True

    def __init__(self, **kwargs):
        self.store = vcstore.VCStore(**kwargs)

        # 修正从 VisualChart 直接复制出来的 symbol
        dataname = self.p.dataname
        if dataname[3].isspace():
            dataname = dataname[0:2] + dataname[4:]
            self.p.dataname = dataname

        self._dataname = '010' + self.p.dataname
        self._mktcode = self.p.dataname[0:3]

        self._tradename = tradename = self.p.tradename or self._dataname
        # 修正从 VisualChart 直接复制出来的 tradename
        if tradename[3].isspace():
            tradename = tradename[0:2] + tradename[4:]
            self._tradename = tradename

    def setenvironment(self, env):
        '''接收 Cerebro 环境，并把它传给所属 store。'''
        super(VCData, self).setenvironment(env)
        env.addstore(self.store)

    def start(self):
        '''启动 VC 连接，并在存在时获取真实 symbol 信息。'''
        super(VCData, self).start()

        self._state = self._ST_START  # 小型有限状态机

        self._newticks = True  # 控制初始 tick 的处理

        self._pingtmout = self.PING_TIMEOUT  # 初始 ping 超时

        self.idx = 1  # dataserie 计数器（VB 从 1 开始）
        self.q = None  # 接收 bar 的队列

        # 市场时间偏移
        self._mktoffset = None
        self._mktoff1 = None
        self._mktoffdiff = None

        if not self.store.connected():
            # 未连接，直接退出
            self.put_notification(self.DISCONNECTED)
            self._state = self._ST_NOTFOUND
            return

        self.put_notification(self.CONNECTED)
        # 获取真实 symbol 信息
        self.qrt = queue.Queue()  # 等待 ping
        self.store._rtdata(self, self._dataname)
        symfound = self.qrt.get()
        if not symfound:
            # 停止后续动作并发出通知
            self.put_notification(self.NOTSUBSCRIBED)
            self.put_notification(self.DISCONNECTED)
            self._state = self._ST_NOTFOUND
            return

        if self.replaying:
            # replaying 时不要向 VC 请求最终 timeframe，而是请求需要 replay 的原始周期
            self._tf, self._comp = self.p.timeframe, self.p.compression
        else:
            # 其他情况（包括 resampling）传递可能已被 filter 修改的最终 timeframe
            self._tf, self._comp = self._timeframe, self._compression,

        self._ticking = self.store._ticking(self._tf)
        self._syminfo = syminfo = self.store._symboldata(self._dataname)

        # 对大多数市场：
        # mktoffset == mktoff1，从返回时间中减去该值即可得到“市场时间”。
        # 如果在 Visual Chart GUI 中切换本地时间/市场时间显示，Visual Chart 会把该值
        # 从 X 改为 0。
        #
        # 但某些市场（至少 096XXX）理论上属于 Europe/London，实际看起来向西偏移了
        # 1 小时，因此需要额外补 1 小时。这些市场也需要 usetimezones=True 才能显示
        # 用户预期的市场时间，因为内部会使用 TZOUTS 定义。

        # 记录并计算市场时间偏移
        self._mktoffset = timedelta(seconds=syminfo.TimeOffset)
        # 非 tick 数据增加 millisecond，把 HH:MM:59.999 推到下一分钟 00.000
        if self.p.millisecond and not self._ticking:
            self._mktoffset -= self.MILLISECOND

        self._mktoff1 = self._mktoffset
        if self._mktcode in self._EXTRA_TIMEOFFSET:
            # 这些代码理论上位于 (UTC+00:00) Dublin/Edinburgh/Lisbon/London，
            # 即 Europe/London；但实验显示时间向西偏移 1 小时，因此额外减 3600 秒
            self._mktoffset -= timedelta(seconds=3600)

        self._mktoffdiff = self._mktoffset - self._mktoff1

        if self._state == self._ST_START:
            self.put_notification(self.DELAYED)

            # 请求数据并获取通信队列
            self.q = self.store._directdata(
                self,
                self._dataname,
                self._tf, self._comp,
                self.p.fromdate, self.p.todate,
                self.p.historical)

            self._state = self._ST_FEEDING

    def stop(self):
        '''停止数据源，并通知 store 停止。'''
        super(VCData, self).stop()
        if self.q:
            self.store._canceldirectdata(self.q)

    def _setserie(self, serie):
        # 接收 serie（COM 对象），用于 ping 事件
        self._serie = serie

    def haslivedata(self):
        return self._laststatus == self.LIVE and self.q

    def _load(self):
        if self._state == self._ST_NOTFOUND:
            return False  # 无法继续处理

        while True:
            try:
                # 只有 resampling/replaying 时 tmout 才不为 0，否则不唤醒
                tmout = self._qcheck * bool(self.resampling)
                msg = self.q.get(timeout=tmout)
            except queue.Empty:
                return None

            if msg is None:
                return False  # 数据流结束

            if msg == self.store._RT_SHUTDOWN:
                self.put_notification(self.DISCONNECTED)
                return False  # VC 已退出

            if msg == self.store._RT_DISCONNECTED:
                self.put_notification(self.CONNBROKEN)
                continue

            if msg == self.store._RT_CONNECTED:
                self.put_notification(self.CONNECTED)
                self.put_notification(self.DELAYED)
                continue

            if msg == self.store._RT_LIVE:
                if self._laststatus != self.LIVE:
                    self.put_notification(self.LIVE)
                continue

            if msg == self.store._RT_DELAYED:
                if self._laststatus != self.DELAYED:
                    self.put_notification(self.DELAYED)
                continue

            if isinstance(msg, integer_types):
                self.put_notification(self.UNKNOWN, msg)
                continue

            # 走到这里时 msg 必然是 bar
            bar = msg

            # 把 tick 写入 bar
            self.lines.open[0] = bar.Open
            self.lines.high[0] = bar.High
            self.lines.low[0] = bar.Low
            self.lines.close[0] = bar.Close
            self.lines.volume[0] = bar.Volume
            self.lines.openinterest[0] = bar.OpenInterest

            # 转换为“市场时间”（含 096 特例）
            dt = self.NULLDATE + timedelta(days=bar.Date) - self._mktoffset
            self.lines.datetime[0] = date2num(dt)

            return True

    #
    # DS 事件
    #
    def _getpingtmout(self):
        '''返回 PumpEvents 唤醒并调用 ping 所需的实际超时时间。

        ping 会检查尚未交付的 bar 是否已经可以交付。VC 可能因为等待新 tick 而卡住
        当前 bar；在交易清淡时，这可能比预期交付时间晚几秒。
        '''
        if self._ticking:
            return -1  # 无超时

        return self._pingtmout

    def OnNewDataSerieBar(self, DataSerie, forcepush=False):
        # 处理 COM 事件；首次创建 data serie 时也会直接调用
        ssize = DataSerie.Size

        if ssize - self.idx > 1:
            # 队列中超过 1 个 bar，说明存在延迟
            if self._laststatus != self.DELAYED:
                self.q.put(self.store._RT_DELAYED)

        # 原始 timeframe 为 ticks 或强制推送时，返回全部内容
        ssize += forcepush or self._ticking
        for idx in range(self.idx, ssize):
            bar = DataSerie.GetBarValues(idx)
            self.q.put(bar)

        if not forcepush and not self._ticking and ssize:
            # 仍有一个 bar 留在当前位置
            dtnow = datetime.now() - self._TOFFSET  # 修正本地时间

            bar = DataSerie.GetBarValues(ssize)
            dt = self.NULLDATE + timedelta(days=bar.Date) - self._mktoffdiff
            if dtnow < dt:
                # bar 已存在但尚未到可交付时间，仍为 LIVE
                if self._laststatus != self.LIVE:
                    self.q.put(self.store._RT_LIVE)

                # 把 ping 超时调整到 bar 边界，并增加少量余量
                self._pingtmout = (dt - dtnow).total_seconds() + 0.5

            else:
                self._pingtmout = self.PING_TIMEOUT  # 没有 bar 剩余，长暂停
                self.q.put(bar)  # 推送 bar 并更新索引
                ssize += 1  # 已推出最后一个 bar

        # 记录最后处理过的 bar
        self.idx = max(1, ssize)

    def ping(self):
        ssize = self._serie.Size

        if self.idx > ssize:
            return  # 没有可用 bar

        if self._laststatus == self.CONNBROKEN:
            self._pingtmout = self.PING_TIMEOUT
            return  # 断线期间不推送

        dtnow = datetime.now() - self._TOFFSET
        # CHECK: ping 时最多应该只有 1 个 bar；即便更多，该算法也不会造成伤害
        for idx in range(self.idx, ssize + 1):  # 到达 ssize
            bar = self._serie.GetBarValues(self.idx)
            # dt = (self.NULLDATE + timedelta(days=bar.Date) + self._mktoff1)
            dt = self.NULLDATE + timedelta(days=bar.Date) - self._mktoffdiff
            if dtnow < dt:
                self._pingtmout = (dt - dtnow).total_seconds() + 0.5
                break  # 还不能交付

            # 把 ping 超时调整到 bar 边界，并增加少量余量
            self._pingtmout = self.PING_TIMEOUT  # 没有 bar，无需检查
            self.q.put(bar)  # 推送 bar 并更新索引
            self.idx += 1

    #
    # RT 事件
    #
    # 可按单个 data 检查连接状态
    if False:
        def OnInternalEvent(self, p1, p2, p3):
            if p1 != 1:  # 看起来是 "Connection Event"
                return

            if p2 == self.lastconn:
                return  # 不重复通知

            self.lastconn = p2  # 保存新的 notification code

            # p2 should be 0 (disconn), 1 (conn)
            self.store._vcrt_connection(self.store._RT_BASEMSG - p2)

    def OnNewTicks(self, ArrayTicks):
        # 处理 New Ticks 的 COM 事件。这里临时用于两个目的：
        #
        # 1. 如果返回 tick.Field == Field_Description，就可以检查请求的 symbol 是否
        #    已找到（tick.Date == 0 表示未找到）。tick.Text 也有 'Not Found'，但更容易
        #    变化。看到 Field_Description 后进入第 2 阶段。
        #
        # 2. 当看到 tick.Field == Field_Time 且 tick.TickIndex == 0 时，表示看到了
        #    某一秒的第一个 tick，可用 tick.Date 计算到 feed server 的时间偏移。后续用
        #    它判断 bar 是否到了交付时间。
        #
        # 完成后会取消 tick 接收

        aticks = ArrayTicks[0]
        # self.debug_ticks(aticks)
        ticks = dict()
        for tick in aticks:
            ticks[tick.Field] = tick

        if self.store.vcrtmod.Field_Description in ticks:
            if self._newticks:
                self._newticks = False
                hasdate = bool(ticks.get(self.store.vcrtmod.Field_Date, False))
                self.qrt.put(hasdate)
                return

        else:
            try:
                tick = ticks[self.store.vcrtmod.Field_Time]
            except KeyError:
                return

            if tick.TickIndex == 0 and self._mktoff1 is not None:
                # 使用 mktoffset 修正 tick 时间（含 096 特例）
                dttick = (self.NULLDATE + timedelta(days=tick.Date) +
                          self._mktoff1)

                self._TOFFSET = datetime.now() - dttick
                if self._mktcode in self._EXTRA_TIMEOFFSET:
                    # 这些代码理论上位于 (UTC+00:00) Dublin/Edinburgh/Lisbon/London，
                    # 即 Europe/London；但实验显示时间向西偏移 1 小时，因此额外减 3600 秒
                    self._TOFFSET -= timedelta(seconds=3600)

                # 取消 tick 接收
                self._vcrt.CancelSymbolFeed(self._dataname, False)

    def debug_ticks(self, ticks):
        print('*' * 50, 'DEBUG OnNewTicks')
        for tick in ticks:
            print('-' * 40)
            print('tick.SymbolCode', tick.SymbolCode.encode('ascii', 'ignore'))
            fname = self.store.vcrtfields.get(tick.Field, tick.Field)
            print('  tick.Field   : {} ({})'.format(fname, tick.Field))
            print('  tick.FieldEx :', tick.FieldEx)
            tdate = tick.Date
            if tdate:
                tdate = self.NULLDATE + timedelta(days=tick.Date)
            print('  tick.Date    :', tdate)

            print('  tick.Index   :', tick.TickIndex)
            print('  tick.Value   :', tick.Value)
            print('  tick.Text    :', tick.Text.encode('ascii', 'ignore'))

#!/usr/bin389/env python
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
import copy
import datetime
import inspect
import itertools
import operator

from .utils.py3 import (filter, keys, integer_types, iteritems, itervalues,
                        map, MAXINT, string_types, with_metaclass)

import backtrader as bt
from .lineiterator import LineIterator, StrategyBase
from .lineroot import LineSingle
from .lineseries import LineSeriesStub
from .metabase import ItemCollection, findowner
from .trade import Trade
from .utils import OrderedDict, AutoOrderedDict, AutoDictList


class MetaStrategy(StrategyBase.__class__):
    _indcol = dict()

    def __new__(meta, name, bases, dct):
        # 兼容 notify_order 的旧方法名
        if 'notify' in dct:
            # 将 'notify' 重命名为 'notify_order'
            dct['notify_order'] = dct.pop('notify')
        if 'notify_operation' in dct:
            # 将 'notify_operation' 重命名为 'notify_trade'
            dct['notify_trade'] = dct.pop('notify_operation')

        return super(MetaStrategy, meta).__new__(meta, name, bases, dct)

    def __init__(cls, name, bases, dct):
        '''类已经创建完成，注册其 subclasses。'''
        # 初始化 class
        super(MetaStrategy, cls).__init__(name, bases, dct)

        if not cls.aliased and \
           name != 'Strategy' and not name.startswith('_'):
            cls._indcol[name] = cls

    def donew(cls, *args, **kwargs):
        _obj, args, kwargs = super(MetaStrategy, cls).donew(*args, **kwargs)

        # 查找 owner 并保存
        _obj.env = _obj.cerebro = cerebro = findowner(_obj, bt.Cerebro)
        _obj._id = cerebro._next_stid()

        return _obj, args, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopreinit(_obj, *args, **kwargs)
        _obj.broker = _obj.env.broker
        _obj._sizer = bt.sizers.FixedSize()
        _obj._orders = list()
        _obj._orderspending = list()
        _obj._trades = collections.defaultdict(AutoDictList)
        _obj._tradespending = list()

        _obj.stats = _obj.observers = ItemCollection()
        _obj.analyzers = ItemCollection()
        _obj._alnames = collections.defaultdict(itertools.count)
        _obj.writers = list()

        _obj._slave_analyzers = list()

        _obj._tradehistoryon = False

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaStrategy, cls).dopostinit(_obj, *args, **kwargs)

        _obj._sizer.set(_obj, _obj.broker)

        return _obj, args, kwargs


class Strategy(with_metaclass(MetaStrategy, StrategyBase)):
    '''用户自定义 strategies 的基类，用于承载交易逻辑和生命周期回调。'''

    _ltype = LineIterator.StratType

    csv = True
    _oldsync = False  # 使用旧方法更新 clock：以 data 0 为准

    # 在 line 中保存最新交付的 data 日期
    lines = ('datetime',)

    def qbuffer(self, savemem=0, replaying=False):
        '''启用 memory saving schemes。

        Args:
          - ``savemem``: 内存节省级别。

            ``0`` 表示不节省内存，每个 lines object 在内存中保存全部值。

            ``1`` 表示所有 lines objects 都节省内存，仅保留严格所需的最小数据。

            负值用于仍然需要 plotting 的场景：

            ``-1`` 表示 Strategy 层级的 Indicators 和 Observers 不启用 memory
            saving，但它们下方声明的对象会启用。

            ``-2`` 在 ``-1`` 基础上，还会为声明了 *plotinfo.plot* 为 ``False``
            的 indicators 启用 memory saving（这些对象不会被绘图）。

          - ``replaying``: 是否处于 replaying 模式。
        '''
        if savemem < 0:
            # 获取所有标记为 Indicator 的属性
            for ind in self._lineiterators[self.IndType]:
                subsave = isinstance(ind, (LineSingle,))
                if not subsave and savemem < -1:
                    subsave = not ind.plotinfo.plot
                ind.qbuffer(savemem=subsave)

        elif savemem > 0:
            for data in self.datas:
                data.qbuffer(replaying=replaying)

            for line in self.lines:
                line.qbuffer(savemem=1)

            # 对依附于 strategy 的所有对象类型启用节省
            for itcls in self._lineiterators:
                for it in self._lineiterators[itcls]:
                    it.qbuffer(savemem=1)

    def _periodset(self):
        dataids = [id(data) for data in self.datas]

        _dminperiods = collections.defaultdict(list)
        for lineiter in self._lineiterators[LineIterator.IndType]:
            # 如果使用多个 datas 且 timeframe 不同，较大的 timeframe
            # 可能会对 next 调用施加更大的时间约束
            clk = getattr(lineiter, '_clock', None)
            if clk is None:
                clk = getattr(lineiter._owner, '_clock', None)
                if clk is None:
                    continue

            while True:
                if id(clk) in dataids:
                    break  # already top-level clock (data feed)

                # 检查当前 clock 是否有更高层级的 clocks
                clk2 = getattr(clk, '_clock', None)
                if clk2 is None:
                    clk2 = getattr(clk._owner, '_clock', None)

                if clk2 is None:
                    break  # 如果找不到 clock，退出

                clk = clk2  # 保留引用并尝试沿层级向上查找

            if clk is None:
                continue  # 找不到 clock，进入下一个

            # LineSeriesStub 包装一条 line，clock 是被包装的 line，而不是 wrapper 自身
            if isinstance(clk, LineSeriesStub):
                clk = clk.lines[0]

            _dminperiods[clk].append(lineiter._minperiod)

        self._minperiods = list()
        for data in self.datas:

            # 不仅把 data 作为 clock，也考虑其 lines；这些 lines 可能被单独作为
            # clock 引用传入，并在上方发现

            # 如果存在 data min period，则用它初始化
            dlminperiods = _dminperiods[data]

            for l in data.lines:  # 在每条 line 中搜索 min periods
                if l in _dminperiods:
                    dlminperiods += _dminperiods[l]  # 找到则加入

            # 如果找到任何引用，则保留到 line 的引用
            _dminperiods[data] = [max(dlminperiods)] if dlminperiods else []

            dminperiod = max(_dminperiods[data] or [data._minperiod])
            self._minperiods.append(dminperiod)

        # 设置 minperiod
        minperiods = \
            [x._minperiod for x in self._lineiterators[LineIterator.IndType]]
        self._minperiod = max(minperiods or [self._minperiod])

    def _addwriter(self, writer):
        '''添加 writer 实例。

        与其他 ``_addxxx`` 函数不同，这里接收实例，因为 writer 工作在 Cerebro
        层级，只是传给 strategy 以简化逻辑。
        '''
        self.writers.append(writer)

    def _addindicator(self, indcls, *indargs, **indkwargs):
        indcls(*indargs, **indkwargs)

    def _addanalyzer_slave(self, ancls, *anargs, **ankwargs):
        '''类似 ``_addanalyzer``，但用于 observers 或其他依赖 analyzer 输出的实体。

        这些 analyzers 不是由用户添加，会与主 analyzers 分开保存。

        Returns:
          Analyzer: 创建出的 analyzer。
        '''
        analyzer = ancls(*anargs, **ankwargs)
        self._slave_analyzers.append(analyzer)
        return analyzer

    def _getanalyzer_slave(self, idx):
        return self._slave_analyzers.append[idx]

    def _addanalyzer(self, ancls, *anargs, **ankwargs):
        anname = ankwargs.pop('_name', '') or ancls.__name__.lower()
        nsuffix = next(self._alnames[anname])
        anname += str(nsuffix or '')  # 0（首个实例）不加 suffix
        analyzer = ancls(*anargs, **ankwargs)
        self.analyzers.append(analyzer, anname)

    def _addobserver(self, multi, obscls, *obsargs, **obskwargs):
        obsname = obskwargs.pop('obsname', '')
        if not obsname:
            obsname = obscls.__name__.lower()

        if not multi:
            newargs = list(itertools.chain(self.datas, obsargs))
            obs = obscls(*newargs, **obskwargs)
            self.stats.append(obs, obsname)
            return

        setattr(self.stats, obsname, list())
        l = getattr(self.stats, obsname)

        for data in self.datas:
            obs = obscls(data, *obsargs, **obskwargs)
            l.append(obs)

    def _getminperstatus(self):
        # 检查与 datas 相关的 min period 状态
        dlens = map(operator.sub, self._minperiods, map(len, self.datas))
        self._minperstatus = minperstatus = max(dlens)
        return minperstatus

    def prenext_open(self):
        pass

    def nextstart_open(self):
        self.next_open()

    def next_open(self):
        pass

    def _oncepost_open(self):
        minperstatus = self._minperstatus
        if minperstatus < 0:
            self.next_open()
        elif minperstatus == 0:
            self.nextstart_open()  # 仅针对第 1 个值调用
        else:
            self.prenext_open()

    def _oncepost(self, dt):
        for indicator in self._lineiterators[LineIterator.IndType]:
            if len(indicator._clock) > len(indicator):
                indicator.advance()

        if self._oldsync:
            # Strategy 尚未 reset，line 仍在当前位置
            self.advance()
        else:
            # strategy 已 reset 到开头，需要逐步 forward
            self.forward()

        self.lines.datetime[0] = dt
        self._notify()

        minperstatus = self._getminperstatus()
        if minperstatus < 0:
            self.next()
        elif minperstatus == 0:
            self.nextstart()  # 仅针对第 1 个值调用
        else:
            self.prenext()

        self._next_analyzers(minperstatus, once=True)
        self._next_observers(minperstatus, once=True)

        self.clear()

    def _clk_update(self):
        if self._oldsync:
            clk_len = super(Strategy, self)._clk_update()
            self.lines.datetime[0] = max(d.datetime[0]
                                         for d in self.datas if len(d))
            return clk_len

        newdlens = [len(d) for d in self.datas]
        if any(nl > l for l, nl in zip(self._dlens, newdlens)):
            self.forward()

        self.lines.datetime[0] = max(d.datetime[0]
                                     for d in self.datas if len(d))
        self._dlens = newdlens

        return len(self)

    def _next_open(self):
        minperstatus = self._minperstatus
        if minperstatus < 0:
            self.next_open()
        elif minperstatus == 0:
            self.nextstart_open()  # 仅针对第 1 个值调用
        else:
            self.prenext_open()

    def _next(self):
        super(Strategy, self)._next()

        minperstatus = self._getminperstatus()
        self._next_analyzers(minperstatus)
        self._next_observers(minperstatus)

        self.clear()

    def _next_observers(self, minperstatus, once=False):
        for observer in self._lineiterators[LineIterator.ObsType]:
            for analyzer in observer._analyzers:
                if minperstatus < 0:
                    analyzer._next()
                elif minperstatus == 0:
                    analyzer._nextstart()  # 仅针对第 1 个值调用
                else:
                    analyzer._prenext()

            if once:
                if len(self) > len(observer):
                    if self._oldsync:
                        observer.advance()
                    else:
                        observer.forward()

                if minperstatus < 0:
                    observer.next()
                elif minperstatus == 0:
                    observer.nextstart()  # 仅针对第 1 个值调用
                elif len(observer):
                    observer.prenext()
            else:
                observer._next()

    def _next_analyzers(self, minperstatus, once=False):
        for analyzer in self.analyzers:
            if minperstatus < 0:
                analyzer._next()
            elif minperstatus == 0:
                analyzer._nextstart()  # 仅针对第 1 个值调用
            else:
                analyzer._prenext()

    def _settz(self, tz):
        self.lines.datetime._settz(tz)

    def _start(self):
        self._periodset()

        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._start()

        for obs in self.observers:
            if not isinstance(obs, list):
                obs = [obs]  # 支持 multi-data observers

            for o in obs:
                o._start()

        # 将 operators 切换到 stage 2
        self._stage2()

        self._dlens = [len(data) for data in self.datas]

        self._minperstatus = MAXINT  # 从 prenext 开始

        self.start()

    def start(self):
        '''在 backtesting 即将开始前调用。'''
        pass

    def getwriterheaders(self):
        self.indobscsv = [self]

        indobs = itertools.chain(
            self.getindicators_lines(), self.getobservers())
        self.indobscsv.extend(filter(lambda x: x.csv, indobs))

        headers = list()

        # 准备 indicators/observers 的 data headers
        for iocsv in self.indobscsv:
            name = iocsv.plotinfo.plotname or iocsv.__class__.__name__
            headers.append(name)
            headers.append('len')
            headers.extend(iocsv.getlinealiases())

        return headers

    def getwritervalues(self):
        values = list()

        for iocsv in self.indobscsv:
            name = iocsv.plotinfo.plotname or iocsv.__class__.__name__
            values.append(name)
            lio = len(iocsv)
            values.append(lio)
            if lio:
                values.extend(map(lambda l: l[0], iocsv.lines.itersize()))
            else:
                values.extend([''] * iocsv.lines.size())

        return values

    def getwriterinfo(self):
        wrinfo = AutoOrderedDict()

        wrinfo['Params'] = self.p._getkwargs()

        sections = [
            ['Indicators', self.getindicators_lines()],
            ['Observers', self.getobservers()]
        ]

        for sectname, sectitems in sections:
            sinfo = wrinfo[sectname]
            for item in sectitems:
                itname = item.__class__.__name__
                sinfo[itname].Lines = item.lines.getlinealiases() or None
                sinfo[itname].Params = item.p._getkwargs() or None

        ainfo = wrinfo.Analyzers

        # 内部 Value Analyzer
        ainfo.Value.Begin = self.broker.startingcash
        ainfo.Value.End = self.broker.getvalue()

        # writer 不输出 slave analyzers
        for aname, analyzer in self.analyzers.getitems():
            ainfo[aname].Params = analyzer.p._getkwargs() or None
            ainfo[aname].Analysis = analyzer.get_analysis()

        return wrinfo

    def _stop(self):
        self.stop()

        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._stop()

        # 将 operators 切回 stage 1，以允许复用 datas
        self._stage1()

    def stop(self):
        '''在 backtesting 即将停止前调用。'''
        pass

    def set_tradehistory(self, onoff=True):
        self._tradehistoryon = onoff

    def clear(self):
        self._orders.extend(self._orderspending)
        self._orderspending = list()
        self._tradespending = list()

    def _addnotification(self, order, quicknotify=False):
        if not order.p.simulated:
            self._orderspending.append(order)

        if quicknotify:
            qorders = [order]
            qtrades = []

        if not order.executed.size:
            if quicknotify:
                self._notify(qorders=qorders, qtrades=qtrades)
            return

        tradedata = order.data._compensate
        if tradedata is None:
            tradedata = order.data

        datatrades = self._trades[tradedata][order.tradeid]
        if not datatrades:
            trade = Trade(data=tradedata, tradeid=order.tradeid,
                          historyon=self._tradehistoryon)
            datatrades.append(trade)
        else:
            trade = datatrades[-1]

        for exbit in order.executed.iterpending():
            if exbit is None:
                break

            if exbit.closed:
                trade.update(order,
                             exbit.closed,
                             exbit.price,
                             exbit.closedvalue,
                             exbit.closedcomm,
                             exbit.pnl,
                             comminfo=order.comminfo)

                if trade.isclosed:
                    self._tradespending.append(copy.copy(trade))
                    if quicknotify:
                        qtrades.append(copy.copy(trade))

            # 按需更新
            if exbit.opened:
                if trade.isclosed:
                    trade = Trade(data=tradedata, tradeid=order.tradeid,
                                  historyon=self._tradehistoryon)
                    datatrades.append(trade)

                trade.update(order,
                             exbit.opened,
                             exbit.price,
                             exbit.openedvalue,
                             exbit.openedcomm,
                             exbit.pnl,
                             comminfo=order.comminfo)

                # 这个额外检查覆盖如下场景：不同 tradeid 的 orders 将 position 降到 0，
                # 而下一个 order “打开” position 的同时又“关闭” trade
                if trade.isclosed:
                    self._tradespending.append(copy.copy(trade))
                    if quicknotify:
                        qtrades.append(copy.copy(trade))

            if trade.justopened:
                self._tradespending.append(copy.copy(trade))
                if quicknotify:
                    qtrades.append(copy.copy(trade))

        if quicknotify:
            self._notify(qorders=qorders, qtrades=qtrades)

    def _notify(self, qorders=[], qtrades=[]):
        if self.cerebro.p.quicknotify:
            # 需要知道 quicknotify 是否开启，以避免重复处理 pendingorders 和 pendingtrades；
            # 它们必须存在，因为 observers 等对象可能会查看它们
            procorders = qorders
            proctrades = qtrades
        else:
            procorders = self._orderspending
            proctrades = self._tradespending

        for order in procorders:
            if order.exectype != order.Historical or order.histnotify:
                self.notify_order(order)
            for analyzer in itertools.chain(self.analyzers,
                                            self._slave_analyzers):
                analyzer._notify_order(order)

        for trade in proctrades:
            self.notify_trade(trade)
            for analyzer in itertools.chain(self.analyzers,
                                            self._slave_analyzers):
                analyzer._notify_trade(trade)

        if qorders:
            return  # cash 会按常规节奏通知

        cash = self.broker.getcash()
        value = self.broker.getvalue()
        fundvalue = self.broker.fundvalue
        fundshares = self.broker.fundshares

        self.notify_cashvalue(cash, value)
        self.notify_fund(cash, value, fundvalue, fundshares)
        for analyzer in itertools.chain(self.analyzers, self._slave_analyzers):
            analyzer._notify_cashvalue(cash, value)
            analyzer._notify_fund(cash, value, fundvalue, fundshares)

    def add_timer(self, when,
                  offset=datetime.timedelta(), repeat=datetime.timedelta(),
                  weekdays=[], weekcarry=False,
                  monthdays=[], monthcarry=True,
                  allow=None,
                  tzdata=None, cheat=False,
                  *args, **kwargs):
        '''添加 strategy 级 timer。

        **注意**：可在 ``__init__`` 或 ``start`` 中调用。

        该方法会安排 timer，在触发时调用当前 strategy 的 ``notify_timer``。

        Args:
          - ``when``: timer 的触发时间，可以是：

            - ``datetime.time`` 实例（见下方 ``tzdata``）。
            - ``bt.timer.SESSION_START``，表示 session 开始。
            - ``bt.timer.SESSION_END``，表示 session 结束。

          - ``offset``: ``datetime.timedelta`` 实例，用于偏移 ``when``。与
            ``SESSION_START`` / ``SESSION_END`` 配合时尤其有意义，例如 session
            开始后 ``15 minutes`` 触发。

          - ``repeat``: ``datetime.timedelta`` 实例。第 1 次触发后，是否在同一
            session 内按该间隔继续调度。超过 session 结束后，会重置为原始 ``when``。

          - ``weekdays``: **已排序** 的整数 iterable，表示 timer 可实际触发的星期；
            ISO code 中 Monday 为 1，Sunday 为 7。未指定时，对所有天生效。

          - ``weekcarry``: 如果为 ``True``，且指定 weekday 未出现（例如交易假日），
            timer 会在下一天执行，即便进入新的一周。

          - ``monthdays``: **已排序** 的整数 iterable，表示每月哪些日期触发 timer，
            例如每月 *15* 日。未指定时，对所有天生效。

          - ``monthcarry``: 如果指定日期未出现（周末、交易假日），timer 会在下一个
            可用日期执行。

          - ``allow``: 可选 callback，接收 ``datetime.date`` 实例，并返回该日期是否
            允许触发 timer。

          - ``tzdata``: 可以为 ``None``、``pytz`` 实例或 ``data feed`` 实例。
            ``None`` 表示按字面解释 ``when``（等同于按 UTC 处理）。传入 ``pytz`` 时，
            ``when`` 按该 timezone 的本地时间解释；传入 ``data feed`` 时，按该 data
            feed 的 ``tz`` 参数解释。

            **注意**：如果 ``when`` 是 ``SESSION_START`` 或 ``SESSION_END`` 且
            ``tzdata`` 为 ``None``，系统会使用第 1 个 *data feed*（即
            ``self.data0``）作为 session 时间参考。

          - ``cheat``: 如果为 ``True``，timer 会在 broker 有机会评估 orders 前触发。
            这允许在 session 开始前基于 opening price 之类的信息发出 orders。

          - ``*args``: 额外位置参数，会传给 ``notify_timer``。
          - ``**kwargs``: 额外关键字参数，会传给 ``notify_timer``。

        Returns:
          Timer: 创建出的 timer。
        '''
        return self.cerebro._add_timer(
            owner=self, when=when, offset=offset, repeat=repeat,
            weekdays=weekdays, weekcarry=weekcarry,
            monthdays=monthdays, monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata, strats=False, cheat=cheat,
            *args, **kwargs)

    def notify_timer(self, timer, when, *args, **kwargs):
        '''接收 timer notification。

        Args:
          - ``timer``: ``add_timer`` 返回的 timer。
          - ``when``: timer 计划触发时间。实际调用时间可能更晚；该值表示 timer time，
            不是系统当前时间。
          - ``*args``: ``add_timer`` 传入的额外位置参数。
          - ``**kwargs``: ``add_timer`` 传入的额外关键字参数。
        '''
        pass

    def notify_cashvalue(self, cash, value):
        '''接收 strategy broker 的当前 cash 和 value 状态。'''
        pass

    def notify_fund(self, cash, value, fundvalue, shares):
        '''接收当前 cash、value、fundvalue 和 fund shares。'''
        pass

    def notify_order(self, order):
        '''当 order 状态变化时接收该 order。'''
        pass

    def notify_trade(self, trade):
        '''当 trade 状态变化时接收该 trade。'''
        pass

    def notify_store(self, msg, *args, **kwargs):
        '''接收来自 store provider 的 notification。'''
        pass

    def notify_data(self, data, status, *args, **kwargs):
        '''接收来自 data 的 notification。'''
        pass

    def getdatanames(self):
        '''返回现有 data names 列表。'''
        return keys(self.env.datasbyname)

    def getdatabyname(self, name):
        '''通过环境（cerebro）按名称返回指定 data。'''
        return self.env.datasbyname[name]

    def cancel(self, order):
        '''在 broker 中取消 order。'''
        self.broker.cancel(order)

    def buy(self, data=None,
            size=None, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            parent=None, transmit=True,
            **kwargs):
        '''创建 buy/long order，并发送给 broker。

        Args:
          - ``data``: order 所属 data。为 ``None`` 时使用系统第 1 个 data，即
            ``self.datas[0]`` / ``self.data0`` / ``self.data``。

          - ``size``: 正数 data units 数量。为 ``None`` 时，通过 ``getsizer`` 取得的
            ``sizer`` 实例自动计算。

          - ``price``: order 使用的价格。live brokers 可能会因为 minimum tick size
            等要求限制格式。``Market`` 和 ``Close`` orders 可使用 ``None``，价格由市场
            决定；对 ``Limit``、``Stop`` 和 ``StopLimit``，该值表示触发点或成交价格。

          - ``plimit``: 仅适用于 ``StopLimit`` orders。``Stop`` 被触发后，用该价格
            设置隐含的 *Limit* order。

          - ``trailamount``: ``StopTrail`` / ``StopTrailLimit`` 使用的绝对 trailing
            stop 距离。

          - ``trailpercent``: ``StopTrail`` / ``StopTrailLimit`` 使用的百分比 trailing
            stop 距离；如果也指定了 ``trailamount``，优先使用 ``trailamount``。

          - ``exectype``: execution type。可选值包括：

            - ``Order.Market`` 或 ``None``: 下一可用价格执行；backtesting 中通常是
              下一根 bar 的 opening price。
            - ``Order.Limit``: 仅在给定 ``price`` 或更优价格执行。
            - ``Order.Stop``: 到达 ``price`` 后触发，并像 ``Market`` order 一样执行。
            - ``Order.StopLimit``: 到达 ``price`` 后触发，并以 ``plimit`` 创建隐含
              *Limit* order。
            - ``Order.Close``: 仅以 session closing price 执行，通常发生在 closing
              auction。
            - ``Order.StopTrail``: 按 ``price`` 减去 ``trailamount`` 或
              ``trailpercent`` 触发，并随价格远离 stop 更新。
            - ``Order.StopTrailLimit``: 类似 ``StopTrail``，但触发后使用 limit 逻辑。

          - ``valid``: order 有效期。``None`` 表示 *Good till cancel*；也可以传入
            ``datetime.datetime`` / ``datetime.date`` 作为 *good till date*；
            ``Order.DAY``、``0`` 或 ``timedelta()`` 表示当日有效到 session 结束；
            numeric value 会按 ``backtrader`` 使用的 matplotlib datetime 编码解释。

          - ``tradeid``: backtrader 内部用于跟踪同一 asset 上重叠 trades 的 id；
            order 状态通知会把它传回 strategy。

          - ``oco``: 另一个 order 实例。当前 order 会加入 OCO（Order Cancel Others）
            组；组内任一 order 执行后，会立即取消其他 orders。

          - ``parent``: order 组的父子关系。例如 bracket order 中，父 buy order
            可被 high-side limit sell 和 low-side stop sell 包围；子 orders 在父 order
            执行前保持 inactive，父 order 取消/过期时子 orders 也会取消。

          - ``transmit``: 是否将 order **transmitted** 给 broker。它可用于控制
            bracket orders，例如先放置父 order 和首批 children，最后一个 child 再触发
            整组 bracket orders 的提交。

          - ``**kwargs``: 额外 broker 参数。backtrader 会把它们传给创建出的 order
            对象。比如 Interactive Brokers 可通过 ``orderType='LIT'``、
            ``lmtPrice=10.0``、``auxPrice=9.8`` 覆盖默认设置，生成
            ``LIMIT IF TOUCHED`` order。

        Returns:
          Order | None: 提交后的 order；如果最终 size 为 0，则返回 ``None``。

        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data if data is not None else self.datas[0]
        size = size if size is not None else self.getsizing(data, isbuy=True)

        if size:
            return self.broker.buy(
                self, data,
                size=abs(size), price=price, plimit=plimit,
                exectype=exectype, valid=valid, tradeid=tradeid, oco=oco,
                trailamount=trailamount, trailpercent=trailpercent,
                parent=parent, transmit=transmit,
                **kwargs)

        return None

    def sell(self, data=None,
             size=None, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             parent=None, transmit=True,
             **kwargs):
        '''创建 sell/short order，并发送给 broker。

        参数含义见 ``buy`` 的说明。

        Returns:
          Order | None: 提交后的 order；如果最终 size 为 0，则返回 ``None``。
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)

        data = data if data is not None else self.datas[0]
        size = size if size is not None else self.getsizing(data, isbuy=False)

        if size:
            return self.broker.sell(
                self, data,
                size=abs(size), price=price, plimit=plimit,
                exectype=exectype, valid=valid, tradeid=tradeid, oco=oco,
                trailamount=trailamount, trailpercent=trailpercent,
                parent=parent, transmit=transmit,
                **kwargs)

        return None

    def close(self, data=None, size=None, **kwargs):
        '''反向下单以关闭 long/short position。

        参数含义见 ``buy`` 的说明。

        Args:
          - ``data``: 要关闭 position 的 data。
          - ``size``: 要关闭的数量；未提供时，会根据现有 position 自动计算。
          - ``**kwargs``: 传给 ``buy`` 或 ``sell`` 的额外参数。

        Returns:
          Order | None: 提交后的 order；没有 position 时返回 ``None``。
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        size = abs(size if size is not None else possize)

        if possize > 0:
            return self.sell(data=data, size=size, **kwargs)
        elif possize < 0:
            return self.buy(data=data, size=size, **kwargs)

        return None

    def buy_bracket(self, data=None, size=None, price=None, plimit=None,
                    exectype=bt.Order.Limit, valid=None, tradeid=0,
                    trailamount=None, trailpercent=None, oargs={},
                    stopprice=None, stopexec=bt.Order.Stop, stopargs={},
                    limitprice=None, limitexec=bt.Order.Limit, limitargs={},
                    **kwargs):
        '''创建 buy bracket order group（low side - buy order - high side）。

        默认行为：

          - 发出 ``Limit`` execution 的 **buy** order。
          - 发出 *low side* ``Stop`` execution 的 bracket **sell** order。
          - 发出 *high side* ``Limit`` execution 的 bracket **sell** order。

        Args:
          - ``data``: order 所属 data；为 ``None`` 时使用第 1 个 data。
          - ``size``: order size；为 ``None`` 时由 ``sizer`` 计算。bracket 的 3 个
            orders 使用同一 size。
          - ``price`` / ``plimit`` / ``trailamount`` / ``trailpercent``:
            含义见 ``buy``。
          - ``exectype`` / ``valid`` / ``tradeid``: 含义见 ``buy``。
          - ``oargs``: 传给主侧 order 的专用关键字参数，会叠加默认 ``**kwargs``。
          - ``stopprice``: *low side* stop order 的指定价格。
          - ``stopexec``: *low side* order 的 execution type；设为 ``None`` 可关闭
            *low side*。
          - ``stopargs``: 传给 *low side* order 的专用关键字参数。
          - ``limitprice``: *high side* limit order 的指定价格。
          - ``limitexec``: *high side* order 的 execution type；设为 ``None`` 可关闭
            *high side*。
          - ``limitargs``: 传给 *high side* order 的专用关键字参数。
          - ``**kwargs``: 传给 3 个 bracket orders 的额外 broker 参数。

        Returns:
          list: 包含 3 个元素 ``[order, stop side, limit side]``。如果关闭了
          high/low side，对应位置仍保留，但值为 ``None``。
        '''

        kargs = dict(size=size,
                     data=data, price=price, plimit=plimit, exectype=exectype,
                     valid=valid, tradeid=tradeid,
                     trailamount=trailamount, trailpercent=trailpercent)
        kargs.update(oargs)
        kargs.update(kwargs)
        kargs['transmit'] = limitexec is None and stopexec is None
        o = self.buy(**kargs)

        if stopexec is not None:
            # low side / stop 侧
            kargs = dict(data=data, price=stopprice, exectype=stopexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(stopargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = limitexec is None
            kargs['size'] = o.size
            ostop = self.sell(**kargs)
        else:
            ostop = None

        if limitexec is not None:
            # high side / limit 侧
            kargs = dict(data=data, price=limitprice, exectype=limitexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(limitargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = True
            kargs['size'] = o.size
            olimit = self.sell(**kargs)
        else:
            olimit = None

        return [o, ostop, olimit]

    def sell_bracket(self, data=None,
                     size=None, price=None, plimit=None,
                     exectype=bt.Order.Limit, valid=None, tradeid=0,
                     trailamount=None, trailpercent=None,
                     oargs={},
                     stopprice=None, stopexec=bt.Order.Stop, stopargs={},
                     limitprice=None, limitexec=bt.Order.Limit, limitargs={},
                     **kwargs):
        '''创建 sell bracket order group（low side - sell order - high side）。

        默认行为：

          - 发出 ``Limit`` execution 的 **sell** order。
          - 发出 *high side* ``Stop`` execution 的 bracket **buy** order。
          - 发出 *low side* ``Limit`` execution 的 bracket **buy** order。

        Args:
          参数含义与 ``buy_bracket`` 对称。

          - ``stopexec=None`` 可关闭 *high side*。
          - ``limitexec=None`` 可关闭 *low side*。

        Returns:
          list: 包含 3 个元素 ``[order, stop side, limit side]``。如果关闭了
          high/low side，对应位置仍保留，但值为 ``None``。
        '''

        kargs = dict(size=size,
                     data=data, price=price, plimit=plimit, exectype=exectype,
                     valid=valid, tradeid=tradeid,
                     trailamount=trailamount, trailpercent=trailpercent)
        kargs.update(oargs)
        kargs.update(kwargs)
        kargs['transmit'] = limitexec is None and stopexec is None
        o = self.sell(**kargs)

        if stopexec is not None:
            # high side / stop 侧
            kargs = dict(data=data, price=stopprice, exectype=stopexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(stopargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = limitexec is None  # 如果是最后一单则 transmit
            kargs['size'] = o.size
            ostop = self.buy(**kargs)
        else:
            ostop = None

        if limitexec is not None:
            # low side / limit 侧
            kargs = dict(data=data, price=limitprice, exectype=limitexec,
                         valid=valid, tradeid=tradeid)
            kargs.update(limitargs)
            kargs.update(kwargs)
            kargs['parent'] = o
            kargs['transmit'] = True
            kargs['size'] = o.size
            olimit = self.buy(**kargs)
        else:
            olimit = None

        return [o, ostop, olimit]

    def order_target_size(self, data=None, target=0, **kwargs):
        '''下单调仓，使 position 最终 size 达到 ``target``。

        当前 ``position`` size 会作为起点参与计算：

          - 如果 ``target`` > ``pos.size``，则 buy ``target - pos.size``。
          - 如果 ``target`` < ``pos.size``，则 sell ``pos.size - target``。

        Args:
          - ``data``: 要调仓的 data。
          - ``target``: 目标 size。
          - ``**kwargs``: 传给 ``buy`` / ``sell`` / ``close`` 的额外参数。

        Returns:
          Order | None: 生成的 order；如果无需下单（``target == position.size``）
          则返回 ``None``。
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        if not target and possize:
            return self.close(data=data, size=possize, **kwargs)

        elif target > possize:
            return self.buy(data=data, size=target - possize, **kwargs)

        elif target < possize:
            return self.sell(data=data, size=possize - target, **kwargs)

        return None  # 无需执行，target == possize

    def order_target_value(self, data=None, target=0.0, price=None, **kwargs):
        '''下单调仓，使 position 最终 value 达到 ``target``。

        当前 ``value`` 会作为起点参与计算：

          - 如果没有 ``target``，则关闭该 data 上的 position。
          - 如果 ``target`` > ``value``，则在该 data 上 buy。
          - 如果 ``target`` < ``value``，则在该 data 上 sell。

        Args:
          - ``data``: 要调仓的 data。
          - ``target``: 目标 value。
          - ``price``: 计算 size 时使用的价格；为 ``None`` 时使用当前 close。
          - ``**kwargs``: 传给 ``buy`` / ``sell`` / ``close`` 的额外参数。

        Returns:
          Order | None: 生成的 order；如果无需下单则返回 ``None``。
        '''

        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        if not target and possize:  # 关闭 position
            return self.close(data=data, size=possize, price=price, **kwargs)

        else:
            value = self.broker.getvalue(datas=[data])
            comminfo = self.broker.getcommissioninfo(data)

            # 确保存在可用价格
            price = price if price is not None else data.close[0]

            if target > value:
                size = comminfo.getsize(price, target - value)
                return self.buy(data=data, size=size, price=price, **kwargs)

            elif target < value:
                size = comminfo.getsize(price, value - target)
                return self.sell(data=data, size=size, price=price, **kwargs)

        return None  # 无需执行，size == possize

    def order_target_percent(self, data=None, target=0.0, **kwargs):
        '''下单调仓，使 position 最终 value 达到当前 portfolio ``value`` 的百分比。

        ``target`` 使用小数表示：``0.05`` 表示 ``5%``。该方法通过
        ``order_target_value`` 执行。

        Args:
          - ``data``: 要调仓的 data。
          - ``target``: 目标百分比。
          - ``**kwargs``: 传给 ``order_target_value`` 的额外参数。

        Returns:
          Order | None: 生成的 order；如果无需下单（``target == position.size``）
          则返回 ``None``。

        ---
        交互界面使用示范例子：

          - 当 ``target=0.05`` 且 portfolio value 为 ``100`` 时，目标 value 为
            ``0.05 * 100 = 5``，随后会把 ``5`` 作为 ``target`` 传给
            ``order_target_value``。
        '''
        if isinstance(data, string_types):
            data = self.getdatabyname(data)
        elif data is None:
            data = self.data

        possize = self.getposition(data, self.broker).size
        target *= self.broker.getvalue()

        return self.order_target_value(data=data, target=target, **kwargs)

    def getposition(self, data=None, broker=None):
        '''返回指定 data 在指定 broker 中的当前 position。

        如果两者都为 ``None``，使用主 data 和默认 broker。

        Returns:
          Position: 当前 position；也可通过 ``position`` property 访问。
        '''
        data = data if data is not None else self.datas[0]
        broker = broker or self.broker
        return broker.getposition(data)

    position = property(getposition)

    def getpositionbyname(self, name=None, broker=None):
        '''返回指定名称 data 在指定 broker 中的当前 position。

        如果两者都为 ``None``，使用主 data 和默认 broker。

        Returns:
          Position: 当前 position；也可通过 ``positionbyname`` property 访问。
        '''
        data = self.datas[0] if not name else self.getdatabyname(name)
        broker = broker or self.broker
        return broker.getposition(data)

    positionbyname = property(getpositionbyname)

    def getpositions(self, broker=None):
        '''直接从 broker 返回按 data 索引的当前 positions。

        如果 ``broker`` 为 ``None``，使用默认 broker。

        Returns:
          dict: 当前 positions；也可通过 ``positions`` property 访问。
        '''
        broker = broker or self.broker
        return broker.positions

    positions = property(getpositions)

    def getpositionsbyname(self, broker=None):
        '''直接从 broker 返回按名称索引的当前 positions。

        如果 ``broker`` 为 ``None``，使用默认 broker。

        Returns:
          OrderedDict: 当前 positions；也可通过 ``positionsbyname`` property 访问。
        '''
        broker = broker or self.broker
        positions = broker.positions

        posbyname = collections.OrderedDict()
        for name, data in iteritems(self.env.datasbyname):
            posbyname[name] = positions[data]

        return posbyname

    positionsbyname = property(getpositionsbyname)

    def _addsizer(self, sizer, *args, **kwargs):
        if sizer is None:
            self.setsizer(bt.sizers.FixedSize())
        else:
            self.setsizer(sizer(*args, **kwargs))

    def setsizer(self, sizer):
        '''替换默认 fixed stake sizer。'''
        self._sizer = sizer
        sizer.set(self, self.broker)
        return sizer

    def getsizer(self):
        '''返回自动 stake 计算时使用的 sizer。

        也可通过 ``sizer`` property 访问。
        '''
        return self._sizer

    sizer = property(getsizer, setsizer)

    def getsizing(self, data=None, isbuy=True):
        '''返回当前情境下由 sizer 实例计算出的 stake。'''
        data = data if data is not None else self.datas[0]
        return self._sizer.getsizing(data, isbuy=isbuy)


class MetaSigStrategy(Strategy.__class__):

    def __new__(meta, name, bases, dct):
        # 将用户定义的 next 映射为 custom，以便先调用自身方法
        if 'next' in dct:
            dct['_next_custom'] = dct.pop('next')

        cls = super(MetaSigStrategy, meta).__new__(meta, name, bases, dct)

        # class 创建后，将 _next_catch 重新映射为 next
        cls.next = cls._next_catch
        return cls

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaSigStrategy, cls).dopreinit(_obj, *args, **kwargs)

        _obj._signals = collections.defaultdict(list)

        _data = _obj.p._data
        if _data is None:
            _obj._dtarget = _obj.data0
        elif isinstance(_data, integer_types):
            _obj._dtarget = _obj.datas[_data]
        elif isinstance(_data, string_types):
            _obj._dtarget = _obj.getdatabyname(_data)
        elif isinstance(_data, bt.LineRoot):
            _obj._dtarget = _data
        else:
            _obj._dtarget = _obj.data0

        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaSigStrategy, cls).dopostinit(_obj, *args, **kwargs)

        for sigtype, sigcls, sigargs, sigkwargs in _obj.p.signals:
            _obj._signals[sigtype].append(sigcls(*sigargs, **sigkwargs))

        # 记录 signal 类型
        _obj._longshort = bool(_obj._signals[bt.SIGNAL_LONGSHORT])

        _obj._long = bool(_obj._signals[bt.SIGNAL_LONG])
        _obj._short = bool(_obj._signals[bt.SIGNAL_SHORT])

        _obj._longexit = bool(_obj._signals[bt.SIGNAL_LONGEXIT])
        _obj._shortexit = bool(_obj._signals[bt.SIGNAL_SHORTEXIT])

        return _obj, args, kwargs


class SignalStrategy(with_metaclass(MetaSigStrategy, Strategy)):
    '''使用 **signals** 自动操作的 ``Strategy`` 子类。

    *Signals* 通常是 indicators，期望输出值含义如下：

      - ``> 0`` 表示 ``long`` 信号。

      - ``< 0`` 表示 ``short`` 信号。

    *Signals* 分为 2 组。

    **Main Group**：

      - ``LONGSHORT``: 同时接受该 signal 的 ``long`` 与 ``short`` 指示。

      - ``LONG``:
        - ``long`` 指示用于做多。
        - ``short`` 指示用于 *close* long position。但：

          - 如果系统中存在 ``LONGEXIT``（见下方）signal，则使用它退出 long。

          - 如果存在 ``SHORT`` signal 且不存在 ``LONGEXIT``，则先用它关闭 ``long``，
            再打开 ``short``。

      - ``SHORT``:
        - ``short`` 指示用于做空。
        - ``long`` 指示用于 *close* short position。但：

          - 如果系统中存在 ``SHORTEXIT``（见下方）signal，则使用它退出 short。

          - 如果存在 ``LONG`` signal 且不存在 ``SHORTEXIT``，则先用它关闭 ``short``，
            再打开 ``long``。

    **Exit Group**：

      这 2 类 signals 用于覆盖其他 signals，并为退出 ``long`` / ``short`` position
      提供条件。

      - ``LONGEXIT``: ``short`` 指示用于退出 ``long`` positions。

      - ``SHORTEXIT``: ``long`` 指示用于退出 ``short`` positions。

    **Order Issuing**

      orders 的 execution type 为 ``Market``，validity 为 ``None``（*Good until
      Canceled*）。

    Args:
      - ``signals``: list/tuple，元素也是 list/tuple，用于实例化 signals 并分配到
        正确类型。通常由 ``cerebro.add_signal`` 管理。

      - ``_accumulate``: 已在市场中时，是否仍允许继续进入市场（long/short）。

      - ``_concurrent``: 已有 orders pending execution 时，是否仍允许继续发出
        orders。

      - ``_data``: 多 datas 场景下 orders 的目标 data。可以是：

        - ``None``: 使用系统中的第 1 个 data。
        - ``int``: 使用插入在该位置的 data。
        - ``str``: 使用创建/添加 data 时传入的 ``name``。
        - ``data`` 实例。

    Returns:
      SignalStrategy: 可根据 signals 自动发出 market orders 的 strategy。
    '''

    params = (
        ('signals', []),
        ('_accumulate', False),
        ('_concurrent', False),
        ('_data', None),
    )

    def _start(self):
        self._sentinel = None  # order concurrency 的 sentinel
        super(SignalStrategy, self)._start()

    def signal_add(self, sigtype, signal):
        self._signals[sigtype].append(signal)

    def _notify(self, qorders=[], qtrades=[]):
        # 如果 order 已完成，则清空 sentinel
        procorders = qorders or self._orderspending
        if self._sentinel is not None:
            for order in procorders:
                if order == self._sentinel and not order.alive():
                    self._sentinel = None
                    break

        super(SignalStrategy, self)._notify(qorders=qorders, qtrades=qtrades)

    def _next_catch(self):
        self._next_signal()
        if hasattr(self, '_next_custom'):
            self._next_custom()

    def _next_signal(self):
        if self._sentinel is not None and not self.p._concurrent:
            return  # order 仍 active，且不允许超过 1 个

        sigs = self._signals
        nosig = [[0.0]]

        # 计算 signals 当前状态
        ls_long = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONGSHORT] or nosig)
        ls_short = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONGSHORT] or nosig)

        l_enter0 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONG] or nosig)
        l_enter1 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONG_INV] or nosig)
        l_enter2 = all(x[0] for x in sigs[bt.SIGNAL_LONG_ANY] or nosig)
        l_enter = l_enter0 or l_enter1 or l_enter2

        s_enter0 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_SHORT] or nosig)
        s_enter1 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_SHORT_INV] or nosig)
        s_enter2 = all(x[0] for x in sigs[bt.SIGNAL_SHORT_ANY] or nosig)
        s_enter = s_enter0 or s_enter1 or s_enter2

        l_ex0 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONGEXIT] or nosig)
        l_ex1 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONGEXIT_INV] or nosig)
        l_ex2 = all(x[0] for x in sigs[bt.SIGNAL_LONGEXIT_ANY] or nosig)
        l_exit = l_ex0 or l_ex1 or l_ex2

        s_ex0 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_SHORTEXIT] or nosig)
        s_ex1 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_SHORTEXIT_INV] or nosig)
        s_ex2 = all(x[0] for x in sigs[bt.SIGNAL_SHORTEXIT_ANY] or nosig)
        s_exit = s_ex0 or s_ex1 or s_ex2

        # 仅在不存在 "xxxExit" 时，使用反向 signals 启动 reversal（先关闭）
        l_rev = not self._longexit and s_enter
        s_rev = not self._shortexit and l_enter

        # 单独 long/short signal 的反向
        l_leav0 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_LONG] or nosig)
        l_leav1 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_LONG_INV] or nosig)
        l_leav2 = all(x[0] for x in sigs[bt.SIGNAL_LONG_ANY] or nosig)
        l_leave = l_leav0 or l_leav1 or l_leav2

        s_leav0 = all(x[0] > 0.0 for x in sigs[bt.SIGNAL_SHORT] or nosig)
        s_leav1 = all(x[0] < 0.0 for x in sigs[bt.SIGNAL_SHORT_INV] or nosig)
        s_leav2 = all(x[0] for x in sigs[bt.SIGNAL_SHORT_ANY] or nosig)
        s_leave = s_leav0 or s_leav1 or s_leav2

        # 如果存在 longexit signals，则让 long leave 失效
        l_leave = not self._longexit and l_leave
        # 如果存在 shortexit signals，则让 short leave 失效
        s_leave = not self._shortexit and s_leave

        # 获取 size 并开始信号逻辑
        size = self.getposition(self._dtarget).size
        if not size:
            if ls_long or l_enter:
                self._sentinel = self.buy(self._dtarget)

            elif ls_short or s_enter:
                self._sentinel = self.sell(self._dtarget)

        elif size > 0:  # 当前 long position
            if ls_short or l_exit or l_rev or l_leave:
                # 关闭 position，与 concurrency 无关
                self.close(self._dtarget)

            if ls_short or l_rev:
                self._sentinel = self.sell(self._dtarget)

            if ls_long or l_enter:
                if self.p._accumulate:
                    self._sentinel = self.buy(self._dtarget)

        elif size < 0:  # 当前 short position
            if ls_long or s_exit or s_rev or s_leave:
                # 关闭 position，与 concurrency 无关
                self.close(self._dtarget)

            if ls_long or s_rev:
                self._sentinel = self.buy(self._dtarget)

            if ls_short or s_enter:
                if self.p._accumulate:
                    self._sentinel = self.sell(self._dtarget)

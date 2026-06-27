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
import collections
import itertools
import multiprocessing

try:  # For new Python versions
    collectionsAbc = collections.abc  # collections.Iterable -> collections.abc.Iterable
except AttributeError:  # For old Python versions
    collectionsAbc = collections  # Используем collections.Iterable

import backtrader as bt
from .utils.py3 import (map, range, zip, with_metaclass, string_types,
                        integer_types)

from . import linebuffer
from . import indicator
from .brokers import BackBroker
from .metabase import MetaParams
from . import observers
from .writer import WriterFile
from .utils import OrderedDict, tzparse, num2date, date2num
from .strategy import Strategy, SignalStrategy
from .tradingcal import (TradingCalendarBase, TradingCalendar,
                         PandasMarketCalendar)
from .timer import Timer

# 定义在这里以便 pickle。理想情况下它可以定义在 Cerebro 内部。


class OptReturn(object):
    '''optimization 返回值容器，用于在 ``optreturn`` 模式下保存精简结果。'''

    def __init__(self, params, **kwargs):
        self.p = self.params = params
        for k, v in kwargs.items():
            setattr(self, k, v)


class Cerebro(with_metaclass(MetaParams, object)):
    '''backtrader 的核心调度引擎。

    该类负责管理 data feeds、strategy、broker、observer、analyzer、writer、
    timer 以及回测/优化运行流程。

    Args:

      - ``preload`` (default: ``True``)

        是否为 strategy 预加载传入 cerebro 的不同 ``data feeds``。

      - ``runonce`` (default: ``True``)

        是否以 vectorized mode 运行 ``Indicators``，以提升整体速度。
        Strategies 和 Observers 始终按 event based 方式运行。

      - ``live`` (default: ``False``)

        如果没有 data 通过 ``islive`` 报告自己是 *live*，但用户仍希望按 ``live`` 模式
        运行，可将该参数设为 ``True``。

        这会同时停用 ``preload`` 和 ``runonce``，但不会影响 memory saving scheme。

        ``Indicators`` 不再按 vectorized mode 运行，而是与 live feed 一样逐步推进。

      - ``maxcpus`` (default: None -> all available cores)

        optimization 时同时使用多少 CPU core。

      - ``stdstats`` (default: ``True``)

        如果为 ``True``，会自动添加默认 Observers：Broker（Cash 和 Value）、Trades
        以及 BuySell。

      - ``oldbuysell`` (default: ``False``)

        当 ``stdstats`` 为 ``True`` 且自动添加 observers 时，该开关控制 ``BuySell``
        observer 的主要行为。

        - ``False``: 使用现代行为，buy/sell signal 分别绘制在 low/high price
          下方/上方，以避免图形拥挤。

        - ``True``: 使用旧行为，把 buy/sell signal 绘制在该时刻 order execution 的
          average price 上。这会覆盖 OHLC bar 或 Line on Close bar，使图形更难识别。

      - ``oldtrades`` (default: ``False``)

        当 ``stdstats`` 为 ``True`` 且自动添加 observers 时，该开关控制 ``Trades``
        observer 的主要行为。

        - ``False``: 使用现代行为，对所有 datas 的 trades 使用不同 marker 绘制。

        - ``True``: 使用旧版 Trades observer，所有 trades 使用相同 marker，仅区分
          正负。

      - ``exactbars`` (default: ``False``)

        默认值下，line 中保存的每个 value 都会保留在内存中。

        可选值：
          - ``True`` or ``1``: 所有 "lines" 对象都会把内存使用量降到自动计算出的
            minimum period。

            例如 Simple Moving Average 的 period 为 30，则底层 data 始终保留 30 根
            bar 的 running buffer，以便计算该 Moving Average。

            - 该设置会停用 ``preload`` 和 ``runonce``。
            - 使用该设置也会停用 **plotting**。

          - ``-1``: strategy 层级的 data feeds 和 indicators/operations 会在内存中
            保留全部 data。

            例如 ``RSI`` 内部使用 ``UpDay`` indicator 计算。这个 subindicator 不会在
            内存中保留全部 data。

            - 这允许保持 ``plotting`` 和 ``preloading`` 激活。

            - ``runonce`` 会被停用。

          - ``-2``: 作为 strategy 属性保存的 data feeds 和 indicators 会在内存中
            保留全部 points。

            例如 ``RSI`` 内部使用 ``UpDay`` indicator 计算。这个 subindicator 不会在
            内存中保留全部 data。

            如果在 ``__init__`` 中定义了类似 ``a = self.data.close - self.data.high``
            的表达式，则 ``a`` 不会在内存中保留全部 data。

            - 这允许保持 ``plotting`` 和 ``preloading`` 激活。

            - ``runonce`` 会被停用。

      - ``objcache`` (default: ``False``)

        实验性选项：为 lines object 实现 cache，以减少对象数量。例如 UltimateOscillator::

          bp = self.data.close - TrueLow(self.data)
          tr = TrueRange(self.data)  # -> 创建另一个 TrueLow(self.data)

        如果为 ``True``，``TrueRange`` 内部第 2 个 ``TrueLow(self.data)`` 与 ``bp``
        计算中的对象签名匹配，则会被复用。

        某些边界场景可能导致 line object 偏离其 minimum period 并破坏计算，因此默认禁用。

      - ``writer`` (default: ``False``)

        如果设为 ``True``，会创建一个默认 ``WriterFile`` 并输出到 stdout。它会被添加
        到 strategy 中，同时不影响用户代码添加的其它 writers。

      - ``tradehistory`` (default: ``False``)

        如果设为 ``True``，会为所有 strategies 中的每个 trade 激活 update event
        logging。也可以在单个 strategy 上通过 ``set_tradehistory`` 实现。

      - ``optdatas`` (default: ``True``)

        如果为 ``True`` 且正在 optimizing，并且系统可以 ``preload`` 且使用 ``runonce``，
        data preloading 只会在主进程中执行一次，以节省时间和资源。

        测试显示大约有 ``20%`` 提速，示例运行从 ``83`` 秒降到 ``66`` 秒。

      - ``optreturn`` (default: ``True``)

        如果为 ``True``，optimization 结果不会返回完整 ``Strategy`` 对象（以及所有
        *datas*、*indicators*、*observers* ...），而是返回带以下属性的精简对象
        （与 ``Strategy`` 中同名）：

          - ``params``（或 ``p``）：本次执行中的 strategy 参数。
          - ``analyzers``：strategy 执行过的 analyzers。

        多数情况下，评估 strategy performance 只需要 *analyzers* 和对应 *params*。
        如果需要详细分析生成的值，例如 *indicators*，请关闭该选项。

        测试显示执行时间提升 ``13% - 15%``。与 ``optdatas`` 组合时，optimization run
        的总提速可达 ``32%``。

      - ``oldsync`` (default: ``False``)

        从 1.9.0.99 开始，多 data（相同或不同 timeframe）的同步机制已改变，以允许
        不同长度的 datas。

        如果希望使用以 data0 作为系统 master 的旧行为，请将该参数设为 ``True``。

      - ``tz`` (default: ``None``)

        为 strategies 添加全局 timezone。``tz`` 可以是：

          - ``None``: strategy 显示的 datetime 为 UTC，这是一直以来的标准行为。

          - ``pytz`` instance: 用于把 UTC time 转换到选定 timezone。

          - ``string``: 会尝试实例化对应 ``pytz`` instance。

          - ``integer``: strategy 使用 ``self.datas`` 中对应 ``data`` 的 timezone；
            ``0`` 表示使用 ``data0`` 的 timezone。

      - ``cheat_on_open`` (default: ``False``)

        会调用 strategy 的 ``next_open`` 方法。它发生在 ``next`` 之前，也发生在 broker
        有机会评估 orders 之前。此时 indicators 尚未重新计算，因此可以基于上一日
        indicators，同时使用 ``open`` price 进行 stake 计算并发出 order。

        对 cheat_on_open order execution，还需要调用 ``cerebro.broker.set_coo(True)``，
        或实例化 ``BackBroker(coo=True)``（*coo* 表示 cheat-on-open），或将
        ``broker_coo`` 设为 ``True``。除非通过下方参数禁用，Cerebro 会自动完成。

      - ``broker_coo`` (default: ``True``)

        当 ``cheat_on_open`` 也为 ``True`` 时，自动调用 broker 的 ``set_coo(True)``
        以激活 ``cheat_on_open`` execution。

      - ``quicknotify`` (default: ``False``)

        Broker notifications 默认会在 *next* prices 交付前送达。对 backtesting 这没有
        影响，但 live broker 中 notification 可能早于 bar 很久发生。设为 ``True`` 时，
        notification 会尽快送达（见 live feeds 中的 ``qcheck``）。

        为兼容性默认设为 ``False``；未来可能改为 ``True``。

    Returns:
      Cerebro: 可配置并运行回测/优化的核心引擎。

    '''

    params = (
        ('preload', True),
        ('runonce', True),
        ('maxcpus', None),
        ('stdstats', True),
        ('oldbuysell', False),
        ('oldtrades', False),
        ('lookahead', 0),
        ('exactbars', False),
        ('optdatas', True),
        ('optreturn', True),
        ('objcache', False),
        ('live', False),
        ('writer', False),
        ('tradehistory', False),
        ('oldsync', False),
        ('tz', None),
        ('cheat_on_open', False),
        ('broker_coo', True),
        ('quicknotify', False),
    )

    def __init__(self):
        self._dolive = False
        self._doreplay = False
        self._dooptimize = False
        self.stores = list()
        self.feeds = list()
        self.datas = list()
        self.datasbyname = collections.OrderedDict()
        self.strats = list()
        self.optcbs = list()  # 保存 opt strategies 的 callback 列表
        self.observers = list()
        self.analyzers = list()
        self.indicators = list()
        self.sizers = dict()
        self.writers = list()
        self.storecbs = list()
        self.datacbs = list()
        self.signals = list()
        self._signal_strat = (None, None, None)
        self._signal_concurrent = False
        self._signal_accumulate = False

        self._dataid = itertools.count(1)

        self._broker = BackBroker()
        self._broker.cerebro = self

        self._tradingcal = None  # TradingCalendar()

        self._pretimers = list()
        self._ohistory = list()
        self._fhistory = None

    @staticmethod
    def iterize(iterable):
        '''把输入元素规范化为可迭代对象。'''
        niterable = list()
        for elem in iterable:
            if isinstance(elem, string_types):
                elem = (elem,)
            elif not isinstance(elem, collectionsAbc.Iterable):  # 不同 Python 版本会调用不同函数
                elem = (elem,)

            niterable.append(elem)

        return niterable

    def set_fund_history(self, fund):
        '''添加 fund history，用于在 broker 中直接执行并评估 performance。

        Args:
          fund: iterable（例如 list、tuple、iterator、generator）。其中每个元素也应是
            有长度的 iterable，包含以下子元素：

            ``[datetime, share_value, net asset value]``

            **注意**：必须按 datetime 升序排序，或生成升序元素。

            其中：

              - ``datetime`` 是 Python ``date/datetime`` 实例，或格式为
                YYYY-MM-DD[THH:MM:SS[.us]] 的字符串；方括号中的元素可选。
              - ``share_value`` 是 float/integer。
              - ``net_asset_value`` 是 float/integer。
        '''
        self._fhistory = fund

    def add_order_history(self, orders, notify=True):
        '''添加 order history，用于在 broker 中直接执行并评估 performance。

        Args:
          orders: iterable（例如 list、tuple、iterator、generator）。其中每个元素也应是
            有长度的 iterable，包含以下子元素（支持 2 种格式）：

            ``[datetime, size, price]`` or ``[datetime, size, price, data]``

            **注意**：必须按 datetime 升序排序，或生成升序元素。

            其中：

              - ``datetime`` 是 Python ``date/datetime`` 实例，或格式为
                YYYY-MM-DD[THH:MM:SS[.us]] 的字符串；方括号中的元素可选。
              - ``size`` 是 integer，正数表示 *buy*，负数表示 *sell*。
              - ``price`` 是 float/integer。
              - ``data`` 如存在，可取以下值：

                - *None*: 使用第 1 个 data feed 作为 target。
                - *integer*: 使用 **Cerebro** 插入顺序中对应 index 的 data。
                - *string*: 使用对应名称的 data，例如通过
                  ``cerebro.adddata(data, name=value)`` 指定的 data。

          notify: 默认 *True*。如果为 ``True``，系统中插入的第 1 个 strategy 会收到
            根据 ``orders`` 中每条信息创建的 artificial order 通知。

        **注意**：这隐含要求添加作为 orders target 的 data feed。例如跟踪 returns 的
        analyzer 会需要该 data。
        '''
        self._ohistory.append((orders, notify))

    def notify_timer(self, timer, when, *args, **kwargs):
        '''接收 timer notification。

        ``timer`` 是 ``add_timer`` 返回的 timer；``when`` 是调用时间。``args`` 和
        ``kwargs`` 是传给 ``add_timer`` 的附加参数。

        实际调用可能晚于 ``when``，因为系统未必能更早调用 timer。该值表示 timer 目标值，
        而不是系统当前时间。
        '''
        pass

    def _add_timer(self, owner, when,
                   offset=datetime.timedelta(), repeat=datetime.timedelta(),
                   weekdays=[], weekcarry=False,
                   monthdays=[], monthcarry=True,
                   allow=None,
                   tzdata=None, strats=False, cheat=False,
                   *args, **kwargs):
        '''创建尚未启动的 timer 的内部方法。'''

        timer = Timer(
            tid=len(self._pretimers),
            owner=owner, strats=strats,
            when=when, offset=offset, repeat=repeat,
            weekdays=weekdays, weekcarry=weekcarry,
            monthdays=monthdays, monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata, cheat=cheat,
            *args, **kwargs
        )

        self._pretimers.append(timer)
        return timer

    def add_timer(self, when,
                  offset=datetime.timedelta(), repeat=datetime.timedelta(),
                  weekdays=[], weekcarry=False,
                  monthdays=[], monthcarry=True,
                  allow=None,
                  tzdata=None, strats=False, cheat=False,
                  *args, **kwargs):
        '''安排 timer 调用 ``notify_timer``。

        Args:

          - ``when``: 可以是：

            - ``datetime.time`` instance (see below ``tzdata``)
            - ``bt.timer.SESSION_START`` to reference a session start
            - ``bt.timer.SESSION_END`` to reference a session end

         - ``offset`` which must be a ``datetime.timedelta`` instance

           用于偏移 ``when``。与 ``SESSION_START`` 和 ``SESSION_END`` 组合时尤其有用，
           例如在 session start 后 ``15 minutes`` 调用 timer。

          - ``repeat`` which must be a ``datetime.timedelta`` instance

            表示首次调用后，是否在同一 session 内按 ``repeat`` 间隔继续安排调用。

            一旦 timer 超过 session end，它会 reset 到 ``when`` 的原始值。

          - ``weekdays``: a **sorted** iterable with integers indicating on
            which days（ISO code，Monday 为 1，Sunday 为 7）timer 可实际调用。

            未指定时，timer 对所有日期有效。

          - ``weekcarry`` (default: ``False``)。如果为 ``True`` 且指定 weekday 未出现
            （例如 trading holiday），timer 会在下一天执行，即使已经进入新的一周。

          - ``monthdays``: a **sorted** iterable with integers indicating on
            which days of the month timer 必须执行。例如每月第 *15* 天。

            未指定时，timer 对所有日期有效。

          - ``monthcarry`` (default: ``True``)。如果指定日期未出现（weekend、trading
            holiday），timer 会在下一个可用日期执行。

          - ``allow`` (default: ``None``)。接收 `datetime.date`` 实例的 callback；
            如果该日期允许 timer，则返回 ``True``，否则返回 ``False``。

          - ``tzdata`` which can be either ``None`` (default), a ``pytz``
            instance 或 ``data feed`` instance。

            ``None``: 按表面值解释 ``when``，即使它不是 UTC，也按类似 UTC 的方式处理。

            ``pytz`` instance: ``when`` 会按该 timezone instance 指定的 local time 解释。

            ``data feed`` instance: ``when`` 会按该 data feed instance 的 ``tz`` 参数
            指定的 local time 解释。

            **注意**：如果 ``when`` 是 ``SESSION_START`` 或 ``SESSION_END`` 且
            ``tzdata`` 为 ``None``，系统中的第 1 个 *data feed*（即 ``self.data0``）
            会作为查找 session times 的 reference。

          - ``strats`` (default: ``False``): 是否同时调用 strategies 的
            ``notify_timer``。

          - ``cheat`` (default ``False``): 如果为 ``True``，timer 会在 broker 有机会
            评估 orders 前调用。例如可在 session start 前基于 opening price 发出 order。
          - ``*args``: 额外 args 会传给 ``notify_timer``。

          - ``**kwargs``: 额外 kwargs 会传给 ``notify_timer``。

        Returns:

          Timer: 创建出的 timer。

        '''
        return self._add_timer(
            owner=self, when=when, offset=offset, repeat=repeat,
            weekdays=weekdays, weekcarry=weekcarry,
            monthdays=monthdays, monthcarry=monthcarry,
            allow=allow,
            tzdata=tzdata, strats=strats, cheat=cheat,
            *args, **kwargs)

    def addtz(self, tz):
        '''添加 strategy 使用的全局 timezone。

        也可以通过参数 ``tz`` 完成同样配置。``tz`` 可以是：

          - ``None``: strategy 显示的 datetime 为 UTC。

          - ``pytz`` instance: 用于把 UTC times 转换到选定 timezone。

          - ``string``: 会尝试实例化 ``pytz`` instance。

          - ``integer``: strategy 使用 ``self.datas`` 中对应 ``data`` 的 timezone；
            ``0`` 使用 ``data0`` 的 timezone。

        '''
        self.p.tz = tz

    def addcalendar(self, cal):
        '''向系统添加全局 trading calendar。

        单个 data feed 可拥有独立 calendar，并覆盖全局 calendar。

        ``cal`` 可以是 ``TradingCalendar`` 实例、字符串，或
        ``pandas_market_calendars`` 实例。字符串会被实例化为 ``PandasMarketCalendar``
        （需要系统中安装 ``pandas_market_calendar``）。

        如果传入 `TradingCalendarBase` 子类而不是实例，该子类会被实例化。
        '''
        if isinstance(cal, string_types):
            cal = PandasMarketCalendar(calendar=cal)
        elif hasattr(cal, 'valid_days'):
            cal = PandasMarketCalendar(calendar=cal)

        else:
            try:
                if issubclass(cal, TradingCalendarBase):
                    cal = cal()
            except TypeError:  # already an instance
                pass

        self._tradingcal = cal

    def add_signal(self, sigtype, sigcls, *sigargs, **sigkwargs):
        '''添加 signal，稍后会交给 ``SignalStrategy`` 使用。'''
        self.signals.append((sigtype, sigcls, sigargs, sigkwargs))

    def signal_strategy(self, stratcls, *args, **kwargs):
        '''添加可接收 signals 的 ``SignalStrategy`` 子类。'''
        self._signal_strat = (stratcls, args, kwargs)

    def signal_concurrent(self, onoff):
        '''设置 signal strategy 是否允许 concurrent orders。'''
        self._signal_concurrent = onoff

    def signal_accumulate(self, onoff):
        '''设置 signal strategy 是否允许已有 position 时继续入场加仓。'''
        self._signal_accumulate = onoff

    def addstore(self, store):
        '''添加 ``Store`` 实例；若已存在则不重复添加。'''
        if store not in self.stores:
            self.stores.append(store)

    def addwriter(self, wrtcls, *args, **kwargs):
        '''添加 ``Writer`` class；实例化会在 ``run`` 时由 cerebro 完成。'''
        self.writers.append((wrtcls, args, kwargs))

    def addsizer(self, sizercls, *args, **kwargs):
        '''添加默认 ``Sizer`` class 和参数，供所有 strategy 使用。'''
        self.sizers[None] = (sizercls, args, kwargs)

    def addsizer_byidx(self, idx, sizercls, *args, **kwargs):
        '''按 ``idx`` 添加 ``Sizer`` class。

        ``idx`` 与 ``addstrategy`` 返回值兼容；只有该 ``idx`` 引用的 strategy 会使用
        该 sizer。
        '''
        self.sizers[idx] = (sizercls, args, kwargs)

    def addindicator(self, indcls, *args, **kwargs):
        '''添加 ``Indicator`` class；会在 ``run`` 时于传入 strategies 中实例化。'''
        self.indicators.append((indcls, args, kwargs))

    def addanalyzer(self, ancls, *args, **kwargs):
        '''添加 ``Analyzer`` class；实例化会在 ``run`` 时完成。'''
        self.analyzers.append((ancls, args, kwargs))

    def addobserver(self, obscls, *args, **kwargs):
        '''添加 ``Observer`` class；实例化会在 ``run`` 时完成。'''
        self.observers.append((False, obscls, args, kwargs))

    def addobservermulti(self, obscls, *args, **kwargs):
        '''添加 per-data ``Observer`` class。

        实例化会在 ``run`` 时完成。它会针对系统中的每个 "data" 添加一次。
        典型用例是观察单个 data 的 buy/sell observer。

        反例是 CashValue，它观察 system-wide values。
        '''
        self.observers.append((True, obscls, args, kwargs))

    def addstorecb(self, callback):
        '''添加 callback，用于接收原本会由 ``notify_store`` 处理的消息。

        callback signature 需支持：

          - ``callback(msg, *args, **kwargs)``

        实际收到的 ``msg``、``*args`` 和 ``**kwargs`` 由实现定义，完全取决于
        *data/broker/store*；通常应假设它们可 *printable*，以便接收和实验。
        '''
        self.storecbs.append(callback)

    def _notify_store(self, msg, *args, **kwargs):
        for callback in self.storecbs:
            callback(msg, *args, **kwargs)

        self.notify_store(msg, *args, **kwargs)

    def notify_store(self, msg, *args, **kwargs):
        '''在 cerebro 中接收 store notifications。

        ``Cerebro`` 子类可以覆盖该方法。

        实际收到的 ``msg``、``*args`` 和 ``**kwargs`` 由实现定义，完全取决于
        *data/broker/store*；通常应假设它们可 *printable*，以便接收和实验。
        '''
        pass

    def _storenotify(self):
        for store in self.stores:
            for notif in store.get_notifications():
                msg, args, kwargs = notif

                self._notify_store(msg, *args, **kwargs)
                for strat in self.runningstrats:
                    strat.notify_store(msg, *args, **kwargs)

    def adddatacb(self, callback):
        '''添加 callback，用于接收原本会由 ``notify_data`` 处理的消息。

        callback signature 需支持：

          - ``callback(data, status, *args, **kwargs)``

        实际收到的 ``*args`` 和 ``**kwargs`` 由实现定义，完全取决于
        *data/broker/store*；通常应假设它们可 *printable*，以便接收和实验。
        '''
        self.datacbs.append(callback)

    def _datanotify(self):
        for data in self.datas:
            for notif in data.get_notifications():
                status, args, kwargs = notif
                self._notify_data(data, status, *args, **kwargs)
                for strat in self.runningstrats:
                    strat.notify_data(data, status, *args, **kwargs)

    def _notify_data(self, data, status, *args, **kwargs):
        for callback in self.datacbs:
            callback(data, status, *args, **kwargs)

        self.notify_data(data, status, *args, **kwargs)

    def notify_data(self, data, status, *args, **kwargs):
        '''在 cerebro 中接收 data notifications。

        ``Cerebro`` 子类可以覆盖该方法。

        实际收到的 ``*args`` 和 ``**kwargs`` 由实现定义，完全取决于
        *data/broker/store*；通常应假设它们可 *printable*，以便接收和实验。
        '''
        pass

    def adddata(self, data, name=None):
        '''添加 ``Data Feed`` 实例。

        如果 ``name`` 非 ``None``，会写入 ``data._name``，用于装饰/绘图用途。
        '''
        if name is not None:
            data._name = name

        data._id = next(self._dataid)
        data.setenvironment(self)

        self.datas.append(data)
        self.datasbyname[data._name] = data
        feed = data.getfeed()
        if feed and feed not in self.feeds:
            self.feeds.append(feed)

        if data.islive():
            self._dolive = True

        return data

    def chaindata(self, *args, **kwargs):
        '''将多个 data feeds 串接为一个 data feed。

        Args:
          - ``*args``: 要串接的 data feed。
          - ``name``: 可选名称；如果提供且非 ``None``，会写入 ``data._name``，
            用于装饰/绘图用途。

        Returns:
          Chainer: 串接后的 data feed；如果未提供 ``name``，使用第 1 个
          data feed 的名称。
        '''
        dname = kwargs.pop('name', None)
        if dname is None:
            dname = args[0]._dataname
        d = bt.feeds.Chainer(dataname=dname, *args)
        self.adddata(d, name=dname)

        return d

    def rolloverdata(self, *args, **kwargs):
        '''将多个 data feeds 通过 RollOver 串接为一个 data feed。

        Args:
          - ``*args``: 要串接的 data feed。
          - ``name``: 可选名称；如果提供且非 ``None``，会写入 ``data._name``，
            用于装饰/绘图用途。
          - ``**kwargs``: 其他参数会传给 ``RollOver`` 类。

        Returns:
          RollOver: 串接后的 data feed；如果未提供 ``name``，使用第 1 个
          data feed 的名称。
        '''
        dname = kwargs.pop('name', None)
        if dname is None:
            dname = args[0]._dataname
        d = bt.feeds.RollOver(dataname=dname, *args, **kwargs)
        self.adddata(d, name=dname)

        return d

    def replaydata(self, dataname, name=None, **kwargs):
        '''添加一个由系统 replay 的 ``Data Feed``。

        Args:
          - ``dataname``: 要 replay 的 data feed；如果它已在系统中，会先 clone。
          - ``name``: 可选名称；如果非 ``None``，会写入 ``data._name``，
            用于装饰/绘图用途。
          - ``**kwargs``: ``timeframe``、``compression``、``todate`` 等 replay
            filter 支持的参数会透明传递。

        Returns:
          DataBase: 已配置 replay 的 data feed。
        '''
        if any(dataname is x for x in self.datas):
            dataname = dataname.clone()

        dataname.replay(**kwargs)
        self.adddata(dataname, name=name)
        self._doreplay = True

        return dataname

    def resampledata(self, dataname, name=None, **kwargs):
        '''添加一个由系统 resample 的 ``Data Feed``。

        Args:
          - ``dataname``: 要 resample 的 data feed；如果它已在系统中，会先 clone。
          - ``name``: 可选名称；如果非 ``None``，会写入 ``data._name``，
            用于装饰/绘图用途。
          - ``**kwargs``: ``timeframe``、``compression``、``todate`` 等 resample
            filter 支持的参数会透明传递。

        Returns:
          DataBase: 已配置 resample 的 data feed。
        '''
        if any(dataname is x for x in self.datas):
            dataname = dataname.clone()

        dataname.resample(**kwargs)
        self.adddata(dataname, name=name)
        self._doreplay = True

        return dataname

    def optcallback(self, cb):
        '''添加 optimization 回调函数。

        每组 strategy 运行完成后，回调会随 optimization 结果一起被调用。

        Args:
          - ``cb``: 回调函数，签名为 ``cb(strategy)``。
        '''
        self.optcbs.append(cb)

    def optstrategy(self, strategy, *args, **kwargs):
        '''添加用于 optimization 的 ``Strategy`` 类。

        strategy 会在 ``run`` 阶段实例化。``args`` 和 ``kwargs`` 必须是
        iterable，用于保存要检查的参数值。

        Args:
          - ``strategy``: 要优化的 ``Strategy`` 类。
          - ``*args``: 位置参数候选值，每个参数都应为 iterable。
          - ``**kwargs``: 关键字参数候选值，每个参数都应为 iterable。

        ---
        交互界面使用示范例子：

          - 如果 strategy 接受 ``period`` 参数，可调用
            ``cerebro.optstrategy(MyStrategy, period=(15, 25))``，系统会分别
            使用 ``15`` 和 ``25`` 执行 optimization。

          - ``cerebro.optstrategy(MyStrategy, period=range(15, 25))`` 会依次
            尝试 ``15`` 到 ``24``；Python 的 ``range`` 是半开区间，不包含
            终点 ``25``。

          - 如果某个参数不需要优化，也仍然用单元素 iterable，例如
            ``cerebro.optstrategy(MyStrategy, period=(15,))``。

          - ``backtrader`` 会尽量识别 ``period=15`` 这类写法，并在可行时
            内部构造伪 iterable。
        '''
        self._dooptimize = True
        args = self.iterize(args)
        optargs = itertools.product(*args)

        optkeys = list(kwargs)

        vals = self.iterize(kwargs.values())
        optvals = itertools.product(*vals)

        okwargs1 = map(zip, itertools.repeat(optkeys), optvals)

        optkwargs = map(dict, okwargs1)

        it = itertools.product([strategy], optargs, optkwargs)
        self.strats.append(it)

    def addstrategy(self, strategy, *args, **kwargs):
        '''添加用于单次运行的 ``Strategy`` 类。

        strategy 会在 ``run`` 阶段实例化，``args`` 和 ``kwargs`` 会原样传给
        strategy 构造函数。

        Args:
          - ``strategy``: 要运行的 ``Strategy`` 类。
          - ``*args``: 传给 strategy 的位置参数。
          - ``**kwargs``: 传给 strategy 的关键字参数。

        Returns:
          int: 本次添加的索引，可供后续添加其他对象（例如 sizers）时引用。
        '''
        self.strats.append([(strategy, args, kwargs)])
        return len(self.strats) - 1

    def setbroker(self, broker):
        '''设置当前 Cerebro 使用的 ``broker`` 实例。

        Args:
          - ``broker``: 要绑定到当前 Cerebro 的 broker 实例。

        Returns:
          BrokerBase: 传入的 broker 实例。
        '''
        self._broker = broker
        broker.cerebro = self
        return broker

    def getbroker(self):
        '''返回当前 broker 实例。

        Returns:
          BrokerBase: 当前 broker 实例；也可以通过 ``broker`` property 访问。
        '''
        return self._broker

    broker = property(getbroker, setbroker)

    def plot(self, plotter=None, numfigs=1, iplot=True, start=None, end=None,
             width=16, height=9, dpi=300, tight=True, use=None,
             **kwargs):
        '''绘制 Cerebro 中的 strategies。

        Args:
          - ``plotter``: 可选 plotter；如果为 ``None``，会创建默认 ``Plot``
            实例，并把 ``kwargs`` 传给它。
          - ``numfigs``: 将图形拆成多少张 chart，可用于降低单张图密度。
          - ``iplot``: 在 notebook 中是否 inline 显示图形。
          - ``start``: 绘图起点，可为 strategy datetime line 的索引，
            或 ``datetime.date`` / ``datetime.datetime`` 实例。
          - ``end``: 绘图终点，可为 strategy datetime line 的索引，
            或 ``datetime.date`` / ``datetime.datetime`` 实例。
          - ``width``: 保存图像的宽度，单位为 inch。
          - ``height``: 保存图像的高度，单位为 inch。
          - ``dpi``: 保存图像的 dots per inch 质量。
          - ``tight``: 是否只保存实际内容而不包含 figure 边框。
          - ``use``: 指定 matplotlib backend；优先级高于 ``iplot``。
          - ``**kwargs``: 创建默认 plotter 时传入的额外参数。

        Returns:
          list: 每个 strategy 绘制出的 figure 列表；如果启用 ``exactbars``，
          不执行绘图。
        '''
        if self._exactbars > 0:
            return

        if not plotter:
            from . import plot
            if self.p.oldsync:
                plotter = plot.Plot_OldSync(**kwargs)
            else:
                plotter = plot.Plot(**kwargs)

        # pfillers = {self.datas[i]: self._plotfillers[i]
        # for i, x in enumerate(self._plotfillers)}

        # pfillers2 = {self.datas[i]: self._plotfillers2[i]
        # for i, x in enumerate(self._plotfillers2)}

        figs = []
        for stratlist in self.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use)
                # pfillers=pfillers2)

                figs.append(rfig)

            plotter.show()

        return figs

    def __call__(self, iterstrat):
        '''optimization 时供 multiprocessing 调用当前 Cerebro 实例。'''

        predata = self.p.optdatas and self._dopreload and self._dorunonce
        return self.runstrategies(iterstrat, predata=predata)

    def __getstate__(self):
        '''optimization 时避免把结果 ``runstrats`` pickle 到子进程。'''

        rv = vars(self).copy()
        if 'runstrats' in rv:
            del(rv['runstrats'])
        return rv

    def runstop(self):
        '''请求尽快停止运行。

        可从 strategy 内部、其他位置甚至其他线程调用。
        '''
        self._event_stop = True  # 标记已经请求 stop

    def run(self, **kwargs):
        '''执行 backtesting 的核心方法。

        Args:
          - ``**kwargs``: 覆盖 Cerebro 初始化时使用的标准参数。

        Returns:
          list: 未启用 optimization 时，返回通过 ``addstrategy`` 添加的
          ``Strategy`` 实例列表；启用 optimization 时，返回包含这些列表的列表。

        如果没有 data，方法会立即返回空列表。
        '''
        self._event_stop = False  # 尚未请求 stop

        if not self.datas:
            return []  # 没有可运行内容

        pkeys = self.params._getkeys()
        for key, val in kwargs.items():
            if key in pkeys:
                setattr(self.params, key, val)

        # 管理对象 cache 的启用/停用
        linebuffer.LineActions.cleancache()  # 清理 cache
        indicator.Indicator.cleancache()  # 清理 cache

        linebuffer.LineActions.usecache(self.p.objcache)
        indicator.Indicator.usecache(self.p.objcache)

        self._dorunonce = self.p.runonce
        self._dopreload = self.p.preload
        self._exactbars = int(self.p.exactbars)

        if self._exactbars:
            self._dorunonce = False  # 启用内存节省模式时不使用 runonce
            self._dopreload = self._dopreload and self._exactbars < 1

        self._doreplay = self._doreplay or any(x.replaying for x in self.datas)
        if self._doreplay:
            # replay 不支持 preloading；完整 timeframe bar 会实时构造
            self._dopreload = False

        if self._dolive or self.p.live:
            # live 模式下 preload 和 runonce 都必须关闭
            self._dorunonce = False
            self._dopreload = False

        self.runwriters = list()

        # 按需添加系统默认 writer
        if self.p.writer is True:
            wr = WriterFile()
            self.runwriters.append(wr)

        # 实例化其他 writers
        for wrcls, wrargs, wrkwargs in self.writers:
            wr = wrcls(*wrargs, **wrkwargs)
            self.runwriters.append(wr)

        # 记录是否有 writer 需要完整 csv 输出
        self.writers_csv = any(map(lambda x: x.p.csv, self.runwriters))

        self.runstrats = list()

        if self.signals:  # allow processing of signals
            signalst, sargs, skwargs = self._signal_strat
            if signalst is None:
                # 尝试判断第 1 个常规 strategy 是否为 signal strategy
                try:
                    signalst, sargs, skwargs = self.strats.pop(0)
                except IndexError:
                    pass  # 没有可取出的 strategy
                else:
                    if not isinstance(signalst, SignalStrategy):
                        # 不是 signal strategy，重新插回开头
                        self.strats.insert(0, (signalst, sargs, skwargs))
                        signalst = None  # 标记为未预设

            if signalst is None:  # recheck
                # 仍然为 None，则创建默认 signal strategy
                signalst, sargs, skwargs = SignalStrategy, tuple(), dict()

            # 添加 signal strategy
            self.addstrategy(signalst,
                             _accumulate=self._signal_accumulate,
                             _concurrent=self._signal_concurrent,
                             signals=self.signals,
                             *sargs,
                             **skwargs)

        if not self.strats:  # 已有 datas 时，添加默认 strategy
            self.addstrategy(Strategy)

        iterstrats = itertools.product(*self.strats)
        if not self._dooptimize or self.p.maxcpus == 1:
            # 未请求 optimization 或只使用 1 个核心时，跳过进程派生
            for iterstrat in iterstrats:
                runstrat = self.runstrategies(iterstrat)
                self.runstrats.append(runstrat)
                if self._dooptimize:
                    for cb in self.optcbs:
                        cb(runstrat)  # callback 接收已完成的 strategy
        else:
            if self.p.optdatas and self._dopreload and self._dorunonce:
                for data in self.datas:
                    data.reset()
                    if self._exactbars < 1:  # datas 可以保留完整长度
                        data.extend(size=self.params.lookahead)
                    data._start()
                    if self._dopreload:
                        data.preload()

            pool = multiprocessing.Pool(self.p.maxcpus or None)
            for r in pool.imap(self, iterstrats):
                self.runstrats.append(r)
                for cb in self.optcbs:
                    cb(r)  # callback 接收已完成的 strategy

            pool.close()

            if self.p.optdatas and self._dopreload and self._dorunonce:
                for data in self.datas:
                    data.stop()

        if not self._dooptimize:
            # 常规运行避免返回 list of list
            return self.runstrats[0]

        return self.runstrats

    def _init_stcount(self):
        self.stcount = itertools.count(0)

    def _next_stid(self):
        return next(self.stcount)

    def runstrategies(self, iterstrat, predata=False):
        '''由 ``run`` 调用的内部方法，用于运行一组 strategies。'''
        self._init_stcount()

        self.runningstrats = runstrats = list()
        for store in self.stores:
            store.start()

        if self.p.cheat_on_open and self.p.broker_coo:
            # 尝试在 broker 中启用 cheat-on-open
            if hasattr(self._broker, 'set_coo'):
                self._broker.set_coo(True)

        if self._fhistory is not None:
            self._broker.set_fund_history(self._fhistory)

        for orders, onotify in self._ohistory:
            self._broker.add_order_history(orders, onotify)

        self._broker.start()

        for feed in self.feeds:
            feed.start()

        if self.writers_csv:
            wheaders = list()
            for data in self.datas:
                if data.csv:
                    wheaders.extend(data.getwriterheaders())

            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addheaders(wheaders)

        # self._plotfillers = [list() for d in self.datas]
        # self._plotfillers2 = [list() for d in self.datas]

        if not predata:
            for data in self.datas:
                data.reset()
                if self._exactbars < 1:  # datas 可以保留完整长度
                    data.extend(size=self.params.lookahead)
                data._start()
                if self._dopreload:
                    data.preload()

        for stratcls, sargs, skwargs in iterstrat:
            sargs = self.datas + list(sargs)
            try:
                strat = stratcls(*sargs, **skwargs)
            except bt.errors.StrategySkipError:
                continue  # 不把该 strategy 加入运行集合

            if self.p.oldsync:
                strat._oldsync = True  # 告知 strategy 使用旧式时钟更新
            if self.p.tradehistory:
                strat.set_tradehistory()
            runstrats.append(strat)

        tz = self.p.tz
        if isinstance(tz, integer_types):
            tz = self.datas[tz]._tz
        else:
            tz = tzparse(tz)

        if runstrats:
            # 为了清晰起见，单独组织循环
            defaultsizer = self.sizers.get(None, (None, None, None))
            for idx, strat in enumerate(runstrats):
                if self.p.stdstats:
                    strat._addobserver(False, observers.Broker)
                    if self.p.oldbuysell:
                        strat._addobserver(True, observers.BuySell)
                    else:
                        strat._addobserver(True, observers.BuySell,
                                           barplot=True)

                    if self.p.oldtrades or len(self.datas) == 1:
                        strat._addobserver(False, observers.Trades)
                    else:
                        strat._addobserver(False, observers.DataTrades)

                for multi, obscls, obsargs, obskwargs in self.observers:
                    strat._addobserver(multi, obscls, *obsargs, **obskwargs)

                for indcls, indargs, indkwargs in self.indicators:
                    strat._addindicator(indcls, *indargs, **indkwargs)

                for ancls, anargs, ankwargs in self.analyzers:
                    strat._addanalyzer(ancls, *anargs, **ankwargs)

                sizer, sargs, skwargs = self.sizers.get(idx, defaultsizer)
                if sizer is not None:
                    strat._addsizer(sizer, *sargs, **skwargs)

                strat._settz(tz)
                strat._start()

                for writer in self.runwriters:
                    if writer.p.csv:
                        writer.addheaders(strat.getwriterheaders())

            if not predata:
                for strat in runstrats:
                    strat.qbuffer(self._exactbars, replaying=self._doreplay)

            for writer in self.runwriters:
                writer.start()

            # 准备 timers
            self._timers = []
            self._timerscheat = []
            for timer in self._pretimers:
                # 按需预处理 tzdata
                timer.start(self.datas[0])

                if timer.params.cheat:
                    self._timerscheat.append(timer)
                else:
                    self._timers.append(timer)

            if self._dopreload and self._dorunonce:
                if self.p.oldsync:
                    self._runonce_old(runstrats)
                else:
                    self._runonce(runstrats)
            else:
                if self.p.oldsync:
                    self._runnext_old(runstrats)
                else:
                    self._runnext(runstrats)

            for strat in runstrats:
                strat._stop()

        self._broker.stop()

        if not predata:
            for data in self.datas:
                data.stop()

        for feed in self.feeds:
            feed.stop()

        for store in self.stores:
            store.stop()

        self.stop_writers(runstrats)

        if self._dooptimize and self.p.optreturn:
            # optimization 结果可以被压缩为轻量返回对象
            results = list()
            for strat in runstrats:
                for a in strat.analyzers:
                    a.strategy = None
                    a._parent = None
                    for attrname in dir(a):
                        if attrname.startswith('data'):
                            setattr(a, attrname, None)

                oreturn = OptReturn(strat.params, analyzers=strat.analyzers, strategycls=type(strat))
                results.append(oreturn)

            return results

        return runstrats

    def stop_writers(self, runstrats):
        cerebroinfo = OrderedDict()
        datainfos = OrderedDict()

        for i, data in enumerate(self.datas):
            datainfos['Data%d' % i] = data.getwriterinfo()

        cerebroinfo['Datas'] = datainfos

        stratinfos = dict()
        for strat in runstrats:
            stname = strat.__class__.__name__
            stratinfos[stname] = strat.getwriterinfo()

        cerebroinfo['Strategies'] = stratinfos

        for writer in self.runwriters:
            writer.writedict(dict(Cerebro=cerebroinfo))
            writer.stop()

    def _brokernotify(self):
        '''驱动 broker，并把 broker 通知分发给 strategy。'''
        self._broker.next()
        while True:
            order = self._broker.get_notification()
            if order is None:
                break

            owner = order.owner
            if owner is None:
                owner = self.runningstrats[0]  # 默认归属

            owner._addnotification(order, quicknotify=self.p.quicknotify)

    def _runnext_old(self, runstrats):
        '''旧同步模式下 full next 运行的实际实现。

        每次 data 到达时，所有对象都会调用自己的 ``next`` 方法。
        '''
        data0 = self.datas[0]
        d0ret = True
        while d0ret or d0ret is None:
            lastret = False
            # 在移动 datas 前先分发 store 通知，因为 store 报错可能导致 datas 不移动
            self._storenotify()
            if self._event_stop:  # 如果已请求 stop
                return
            self._datanotify()
            if self._event_stop:  # 如果已请求 stop
                return

            d0ret = data0.next()
            if d0ret:
                for data in self.datas[1:]:
                    if not data.next(datamaster=data0):  # 没有输出
                        data._check(forcedata=data0)  # 检查是否强制输出
                        data.next(datamaster=data0)  # 重试

            elif d0ret is None:
                # live feeds 之类的数据源可能暂时不产生 bar，但仍需要循环继续，
                # 以便处理通知，并让 resample 等逻辑及时产出 bars
                data0._check()
                for data in self.datas[1:]:
                    data._check()
            else:
                lastret = data0._last()
                for data in self.datas[1:]:
                    lastret += data._last(datamaster=data0)

                if not lastret:
                    # 只有 "lasts" 改变了内容时，才额外运行一轮
                    break

            # datas 在 next 后可能生成了新通知
            self._datanotify()
            if self._event_stop:  # 如果已请求 stop
                return

            self._brokernotify()
            if self._event_stop:  # 如果已请求 stop
                return

            if d0ret or lastret:  # data 或 filters 产出了 bars
                for strat in runstrats:
                    strat._next()
                    if self._event_stop:  # 如果已请求 stop
                        return

                    self._next_writers(runstrats)

        # 停止前最后一次处理通知
        self._datanotify()
        if self._event_stop:  # 如果已请求 stop
            return
        self._storenotify()
        if self._event_stop:  # 如果已请求 stop
            return

    def _runonce_old(self, runstrats):
        '''旧同步模式下 vector 运行的实际实现。

        strategies 仍然通过伪事件模式调用，每次 data 到达时触发 ``next``。
        '''
        for strat in runstrats:
            strat._once()

        # strategy 默认的 once 不做任何事，因此不会推进调用 once 前归位的
        # datas/indicators/observers；这里也无需再次推进，因为指针仍在 0
        data0 = self.datas[0]
        datas = self.datas[1:]
        for i in range(data0.buflen()):
            data0.advance()
            for data in datas:
                data.advance(datamaster=data0)

            self._brokernotify()
            if self._event_stop:  # 如果已请求 stop
                return

            for strat in runstrats:
                # data0.datetime[0] 用于兼容新版 strategy 的 oncepost
                strat._oncepost(data0.datetime[0])
                if self._event_stop:  # 如果已请求 stop
                    return

                self._next_writers(runstrats)

    def _next_writers(self, runstrats):
        if not self.runwriters:
            return

        if self.writers_csv:
            wvalues = list()
            for data in self.datas:
                if data.csv:
                    wvalues.extend(data.getwritervalues())

            for strat in runstrats:
                wvalues.extend(strat.getwritervalues())

            for writer in self.runwriters:
                if writer.p.csv:
                    writer.addvalues(wvalues)

                    writer.next()

    def _disable_runonce(self):
        '''供 lineiterators 禁用 runonce 的 API（参见 HeikinAshi）。'''
        self._dorunonce = False

    def _runnext(self, runstrats):
        '''full next 模式下运行的实际实现。

        每次 data 到达时，所有对象都会调用自己的 ``next`` 方法。
        '''
        datas = sorted(self.datas,
                       key=lambda x: (x._timeframe, x._compression))
        datas1 = datas[1:]
        data0 = datas[0]
        d0ret = True

        rs = [i for i, x in enumerate(datas) if x.resampling]
        rp = [i for i, x in enumerate(datas) if x.replaying]
        rsonly = [i for i, x in enumerate(datas)
                  if x.resampling and not x.replaying]
        onlyresample = len(datas) == len(rsonly)
        noresample = not rsonly

        clonecount = sum(d._clone for d in datas)
        ldatas = len(datas)
        ldatas_noclones = ldatas - clonecount
        lastqcheck = False
        dt0 = date2num(datetime.datetime.max) - 2  # 默认接近最大时间
        while d0ret or d0ret is None:
            # 如果任一 data 在 buffer 中有 live data，则所有 data 都不等待
            newqcheck = not any(d.haslivedata() for d in datas)
            if not newqcheck:
                # 如果没有 data 进入 live 状态，或全部已进入，则等待下一批 data
                livecount = sum(d._laststatus == d.LIVE for d in datas)
                newqcheck = not livecount or livecount == ldatas_noclones

            lastret = False
            # 在移动 datas 前先分发 store 通知，因为 store 报错可能导致 datas 不移动
            self._storenotify()
            if self._event_stop:  # 如果已请求 stop
                return
            self._datanotify()
            if self._event_stop:  # 如果已请求 stop
                return

            # 记录起始时间，并告知 feeds 从 qcheck 中扣除已耗费时间
            drets = []
            qstart = datetime.datetime.utcnow()
            for d in datas:
                qlapse = datetime.datetime.utcnow() - qstart
                d.do_qcheck(newqcheck, qlapse.total_seconds())
                drets.append(d.next(ticks=False))

            d0ret = any((dret for dret in drets))
            if not d0ret and any((dret is None for dret in drets)):
                d0ret = None

            if d0ret:
                dts = []
                for i, ret in enumerate(drets):
                    dts.append(datas[i].datetime[0] if ret else None)

                # 找到最小 datetime 的索引
                if onlyresample or noresample:
                    dt0 = min((d for d in dts if d is not None))
                else:
                    dt0 = min((d for i, d in enumerate(dts)
                               if d is not None and i not in rsonly))

                dmaster = datas[dts.index(dt0)]  # 同时作为 timemaster
                self._dtmaster = dmaster.num2date(dt0)
                self._udtmaster = num2date(dt0)

                # slen = len(runstrats[0])
                # 尝试为没有返回的 data 取得输出
                for i, ret in enumerate(drets):
                    if ret:  # dts 已包含该索引的有效 datetime
                        continue

                    # 通过 master 检查，尝试让 data 输出
                    d = datas[i]
                    d._check(forcedata=dmaster)  # 检查是否强制输出
                    if d.next(datamaster=dmaster, ticks=False):  # 重试
                        dts[i] = d.datetime[0]  # 成功则保存
                        # self._plotfillers2[i].append(slen)  # 标记为填充
                    else:
                        # self._plotfillers[i].append(slen)  # 标记为空
                        pass

                # 确保最终只有处于 dmaster 层级的 data 交付输出
                for i, dti in enumerate(dts):
                    if dti is not None:
                        di = datas[i]
                        rpi = False and di.replaying   # 用于检查行为
                        if dti > dt0:
                            if not rpi:  # 必须看到所有 ticks
                                di.rewind()  # 还不能交付
                            # self._plotfillers[i].append(slen)
                        elif not di.replaying:
                            # replay 会强制 tick fill，否则在这里强制
                            di._tick_fill(force=True)

                        # self._plotfillers2[i].append(slen)  # 标记为填充

            elif d0ret is None:
                # live feeds 之类的数据源可能暂时不产生 bar，但仍需要循环继续，
                # 以便处理通知，并让 resample 等逻辑及时产出 bars
                for data in datas:
                    data._check()
            else:
                lastret = data0._last()
                for data in datas1:
                    lastret += data._last(datamaster=data0)

                if not lastret:
                    # 只有 "lasts" 改变了内容时，才额外运行一轮
                    break

            # datas 在 next 后可能生成了新通知
            self._datanotify()
            if self._event_stop:  # 如果已请求 stop
                return

            if d0ret or lastret:  # 只要有 bar，就在 broker 前检查 timers
                self._check_timers(runstrats, dt0, cheat=True)
                if self.p.cheat_on_open:
                    for strat in runstrats:
                        strat._next_open()
                        if self._event_stop:  # 如果已请求 stop
                            return

            self._brokernotify()
            if self._event_stop:  # 如果已请求 stop
                return

            if d0ret or lastret:  # data 或 filters 产出了 bars
                self._check_timers(runstrats, dt0, cheat=False)
                for strat in runstrats:
                    strat._next()
                    if self._event_stop:  # 如果已请求 stop
                        return

                    self._next_writers(runstrats)

        # 停止前最后一次处理通知
        self._datanotify()
        if self._event_stop:  # 如果已请求 stop
            return
        self._storenotify()
        if self._event_stop:  # 如果已请求 stop
            return

    def _runonce(self, runstrats):
        '''vector 模式下运行的实际实现。

        strategies 仍然通过伪事件模式调用，每次 data 到达时触发 ``next``。
        '''
        for strat in runstrats:
            strat._once()
            strat.reset()  # strategy 接下来会被 next 调用，重置 lines

        # strategy 默认的 once 不做任何事，因此不会推进调用 once 前归位的
        # datas/indicators/observers；这里也无需再次推进，因为指针仍在 0
        datas = sorted(self.datas,
                       key=lambda x: (x._timeframe, x._compression))

        while True:
            # 检查 datas 中下一个到达日期
            dts = [d.advance_peek() for d in datas]
            dt0 = min(dts)
            if dt0 == float('inf'):
                break  # 没有 data 会继续交付内容

            # 按需获取 timemaster
            # dmaster = datas[dts.index(dt0)]  # 同时作为 timemaster
            slen = len(runstrats[0])
            for i, dti in enumerate(dts):
                if dti <= dt0:
                    datas[i].advance()
                    # self._plotfillers2[i].append(slen)  # 标记为填充
                else:
                    # self._plotfillers[i].append(slen)
                    pass

            self._check_timers(runstrats, dt0, cheat=True)

            if self.p.cheat_on_open:
                for strat in runstrats:
                    strat._oncepost_open()
                    if self._event_stop:  # 如果已请求 stop
                        return

            self._brokernotify()
            if self._event_stop:  # 如果已请求 stop
                return

            self._check_timers(runstrats, dt0, cheat=False)

            for strat in runstrats:
                strat._oncepost(dt0)
                if self._event_stop:  # 如果已请求 stop
                    return

                self._next_writers(runstrats)

    def _check_timers(self, runstrats, dt0, cheat=False):
        timers = self._timers if not cheat else self._timerscheat
        for t in timers:
            if not t.check(dt0):
                continue

            t.params.owner.notify_timer(t, t.lastwhen, *t.args, **t.kwargs)

            if t.params.strats:
                for strat in runstrats:
                    strat.notify_timer(t, t.lastwhen, *t.args, **t.kwargs)

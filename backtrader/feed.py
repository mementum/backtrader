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
import datetime
import inspect
import io
import os.path

import backtrader as bt
from backtrader import (date2num, num2date, time2num, TimeFrame, dataseries,
                        metabase)

from backtrader.utils.py3 import with_metaclass, zip, range, string_types
from backtrader.utils import tzparse
from .dataseries import SimpleFilterWrapper
from .resamplerfilter import Resampler, Replayer
from .tradingcal import PandasMarketCalendar


class MetaAbstractDataBase(dataseries.OHLCDateTime.__class__):
    '''DataBase metaclass 的基类，用于登记 data feed 子类并完成初始化挂接。'''

    _indcol = dict()

    def __init__(cls, name, bases, dct):
        '''类已创建完成，登记 data feed 子类。'''
        # 初始化类
        super(MetaAbstractDataBase, cls).__init__(name, bases, dct)

        if not cls.aliased and \
           name != 'DataBase' and not name.startswith('_'):
            cls._indcol[name] = cls

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaAbstractDataBase, cls).dopreinit(_obj, *args, **kwargs)

        # 查找 owner 并保存
        _obj._feed = metabase.findowner(_obj, FeedBase)

        _obj.notifs = collections.deque()  # 保存发给 cerebro 的 notifications

        _obj._dataname = _obj.p.dataname
        _obj._name = ''
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = \
            super(MetaAbstractDataBase, cls).dopostinit(_obj, *args, **kwargs)

        # 使用子类设置的名称、参数名称，或 dataname（ticker）
        _obj._name = _obj._name or _obj.p.name
        if not _obj._name and isinstance(_obj.p.dataname, string_types):
            _obj._name = _obj.p.dataname
        _obj._compression = _obj.p.compression
        _obj._timeframe = _obj.p.timeframe

        if isinstance(_obj.p.sessionstart, datetime.datetime):
            _obj.p.sessionstart = _obj.p.sessionstart.time()

        elif _obj.p.sessionstart is None:
            _obj.p.sessionstart = datetime.time.min

        if isinstance(_obj.p.sessionend, datetime.datetime):
            _obj.p.sessionend = _obj.p.sessionend.time()

        elif _obj.p.sessionend is None:
            # 减少 9 微秒以避免 precision rounding errors
            _obj.p.sessionend = datetime.time(23, 59, 59, 999990)

        if isinstance(_obj.p.fromdate, datetime.date):
            # 推到当天 sessionstart，否则日内数据在当天结束前的值会被过滤掉
            if not hasattr(_obj.p.fromdate, 'hour'):
                _obj.p.fromdate = datetime.datetime.combine(
                    _obj.p.fromdate, _obj.p.sessionstart)

        if isinstance(_obj.p.todate, datetime.date):
            # 推到当天 sessionend，否则日内数据在当天结束前的值会被过滤掉
            if not hasattr(_obj.p.todate, 'hour'):
                _obj.p.todate = datetime.datetime.combine(
                    _obj.p.todate, _obj.p.sessionend)

        _obj._barstack = collections.deque()  # 用于 filter operations
        _obj._barstash = collections.deque()  # 用于 filter operations

        _obj._filters = list()
        _obj._ffilters = list()
        for fp in _obj.p.filters:
            if inspect.isclass(fp):
                fp = fp(_obj)
                if hasattr(fp, 'last'):
                    _obj._ffilters.append((fp, [], {}))

            _obj._filters.append((fp, [], {}))

        return _obj, args, kwargs


class AbstractDataBase(with_metaclass(MetaAbstractDataBase,
                                      dataseries.OHLCDateTime)):
    '''data feed 的抽象基类，用于管理时间过滤、通知、filter 和 bar 加载流程。'''

    params = (
        ('dataname', None),
        ('name', ''),
        ('compression', 1),
        ('timeframe', TimeFrame.Days),
        ('fromdate', None),
        ('todate', None),
        ('sessionstart', None),
        ('sessionend', None),
        ('filters', []),
        ('tz', None),
        ('tzinput', None),
        ('qcheck', 0.0),  # 检查 event 的超时时间，单位为秒（float）
        ('calendar', None),
    )

    (CONNECTED, DISCONNECTED, CONNBROKEN, DELAYED,
     LIVE, NOTSUBSCRIBED, NOTSUPPORTED_TF, UNKNOWN) = range(8)

    _NOTIFNAMES = [
        'CONNECTED', 'DISCONNECTED', 'CONNBROKEN', 'DELAYED',
        'LIVE', 'NOTSUBSCRIBED', 'NOTSUPPORTED_TIMEFRAME', 'UNKNOWN']

    @classmethod
    def _getstatusname(cls, status):
        return cls._NOTIFNAMES[status]

    _compensate = None
    _feed = None
    _store = None

    _clone = False
    _qcheck = 0.0

    _tmoffset = datetime.timedelta()

    # resampling/replaying 时设为非 0
    resampling = 0
    replaying = 0

    _started = False

    def _start_finish(self):
        # live feed 可能在 start 后才知道 timezone 信息，因此 date/time 相关参数
        # 在这个较晚阶段统一转换。
        # 获取输出 timezone（如果有）
        self._tz = self._gettz()
        # Lines 已经创建，设置 tz
        self.lines.datetime._settz(self._tz)

        # 这也许也应该由一个可覆盖方法调用
        self._tzinput = bt.utils.date.Localizer(self._gettzinput())

        # 将用户输入时间转换到输出 timezone（或 min/max）
        if self.p.fromdate is None:
            self.fromdate = float('-inf')
        else:
            self.fromdate = self.date2num(self.p.fromdate)

        if self.p.todate is None:
            self.todate = float('inf')
        else:
            self.todate = self.date2num(self.p.todate)

        # FIXME: 这两个值从未使用，可以移除
        self.sessionstart = time2num(self.p.sessionstart)
        self.sessionend = time2num(self.p.sessionend)

        self._calendar = cal = self.p.calendar
        if cal is None:
            self._calendar = self._env._tradingcal
        elif isinstance(cal, string_types):
            self._calendar = PandasMarketCalendar(calendar=cal)

        self._started = True

    def _start(self):
        self.start()

        if not self._started:
            self._start_finish()

    def _timeoffset(self):
        return self._tmoffset

    def _getnexteos(self):
        '''使用 trading calendar 返回下一个 end-of-session（如果可用）。'''
        if self._clone:
            return self.data._getnexteos()

        if not len(self):
            return datetime.datetime.min, 0.0

        dt = self.lines.datetime[0]
        dtime = num2date(dt)
        if self._calendar is None:
            nexteos = datetime.datetime.combine(dtime, self.p.sessionend)
            nextdteos = self.date2num(nexteos)  # localized -> utc-like
            nexteos = num2date(nextdteos)  # utc
            while dtime > nexteos:
                nexteos += datetime.timedelta(days=1)  # 已经是 utc-like

            nextdteos = date2num(nexteos)  # -> utc-like

        else:
            # 返回 utc 时间
            _, nexteos = self._calendar.schedule(dtime, self._tz)
            nextdteos = date2num(nexteos)  # nextos is already utc

        return nexteos, nextdteos

    def _gettzinput(self):
        '''供子类覆盖，用于返回输入 timezone。'''
        return tzparse(self.p.tzinput)

    def _gettz(self):
        '''供可自动计算 timezone 的子类覆盖。'''
        return tzparse(self.p.tz)

    def date2num(self, dt):
        if self._tz is not None:
            return date2num(self._tz.localize(dt))

        return date2num(dt)

    def num2date(self, dt=None, tz=None, naive=True):
        if dt is None:
            return num2date(self.lines.datetime[0], tz or self._tz, naive)

        return num2date(dt, tz or self._tz, naive)

    def haslivedata(self):
        return False  # 支持 live data 的子类必须覆盖

    def do_qcheck(self, onoff, qlapse):
        # onoff 为 True 时，data 会在队列上等待 p.qcheck，以接收 live data。
        qwait = self.p.qcheck if onoff else 0.0
        qwait = max(0.0, qwait - qlapse)
        self._qcheck = qwait

    def islive(self):
        '''返回该 data feed 是否为 live feed。

        如果返回 ``True``，``Cerebro`` 会停用 ``preload`` 和 ``runonce``，因为 live
        data source 必须逐 tick（或逐 bar）获取。
        '''
        return False

    def put_notification(self, status, *args, **kwargs):
        '''向 notification queue 添加状态通知。'''
        if self._laststatus != status:
            self.notifs.append((status, args, kwargs))
            self._laststatus = status

    def get_notifications(self):
        '''返回待处理的 data notification。'''
        # 后台线程可能持续添加 notification。None 标记用于识别本轮最后一个待交付项。
        self.notifs.append(None)  # 放置标记
        notifs = list()
        while True:
            notif = self.notifs.popleft()
            if notif is None:  # 到达标记
                break
            notifs.append(notif)

        return notifs

    def getfeed(self):
        return self._feed

    def qbuffer(self, savemem=0, replaying=False):
        extrasize = self.resampling or replaying
        for line in self.lines:
            line.qbuffer(savemem=savemem, extrasize=extrasize)

    def start(self):
        self._barstack = collections.deque()
        self._barstash = collections.deque()
        self._laststatus = self.CONNECTED

    def stop(self):
        pass

    def clone(self, **kwargs):
        return DataClone(dataname=self, **kwargs)

    def copyas(self, _dataname, **kwargs):
        d = DataClone(dataname=self, **kwargs)
        d._dataname = _dataname
        d._name = _dataname
        return d

    def setenvironment(self, env):
        '''保存 environment 引用。'''
        self._env = env

    def getenvironment(self):
        return self._env

    def addfilter_simple(self, f, *args, **kwargs):
        fp = SimpleFilterWrapper(self, f, *args, **kwargs)
        self._filters.append((fp, fp.args, fp.kwargs))

    def addfilter(self, p, *args, **kwargs):
        if inspect.isclass(p):
            pobj = p(self, *args, **kwargs)
            self._filters.append((pobj, [], {}))

            if hasattr(pobj, 'last'):
                self._ffilters.append((pobj, [], {}))

        else:
            self._filters.append((p, args, kwargs))

    def compensate(self, other):
        '''告知 broker：该资产上的操作会抵消另一个资产的 open position。'''

        self._compensate = other

    def _tick_nullify(self):
        # 这些是 new bar 被“更新”时使用的更新价格。
        # 例如 replay 正在发生，或 real-time data feed 用 5 秒更新构造 1 分钟 bar，
        # 此时长度不会变化。
        for lalias in self.getlinealiases():
            if lalias != 'datetime':
                setattr(self, 'tick_' + lalias, None)

        self.tick_last = None

    def _tick_fill(self, force=False):
        # 如果没有填充 tick_xxx 属性，则当前 bar 本身就是 tick
        alias0 = self._getlinealias(0)
        if force or getattr(self, 'tick_' + alias0, None) is None:
            for lalias in self.getlinealiases():
                if lalias != 'datetime':
                    setattr(self, 'tick_' + lalias,
                            getattr(self.lines, lalias)[0])

            self.tick_last = getattr(self.lines, alias0)[0]

    def advance_peek(self):
        if len(self) < self.buflen():
            return self.lines.datetime[1]  # 返回未来时间

        return float('inf')  # 否则返回最大日期

    def advance(self, size=1, datamaster=None, ticks=True):
        if ticks:
            self._tick_nullify()

        # 需要拦截该调用，以支持不同长度（timeframes）的 data
        self.lines.advance(size)

        if datamaster is not None:
            if len(self) > self.buflen():
                # 没有 bar 可交付时，填充一个 empty bar
                self.rewind()
                self.lines.forward()
                return

            if self.lines.datetime[0] > datamaster.lines.datetime[0]:
                self.lines.rewind()
            else:
                if ticks:
                    self._tick_fill()
        elif len(self) < self.buflen():
            # resampler 可能已经把当前位置 advance 到最后一个点之后
            if ticks:
                self._tick_fill()

    def next(self, datamaster=None, ticks=True):

        if len(self) >= self.buflen():
            if ticks:
                self._tick_nullify()

            # 未 preload，直接请求下一根 bar
            ret = self.load()
            if not ret:
                # 如果 load 无法生成 bar，直接转发结果
                return ret

            if datamaster is None:
                # bar 已存在且无 master，返回 load 的结果
                if ticks:
                    self._tick_fill()
                return ret
        else:
            self.advance(ticks=ticks)

        # bar 已“loaded”或已 preload，索引已移动到该位置
        if datamaster is not None:
            # 存在时间参考，需要对齐检查
            if self.lines.datetime[0] > datamaster.lines.datetime[0]:
                # 时间过早，无法交付 new bar，回退
                self.rewind()
                return False
            else:
                if ticks:
                    self._tick_fill()

        else:
            if ticks:
                self._tick_fill()

        # 告知外部已有 bar（新的或上一根）
        return True

    def preload(self):
        while self.load():
            pass

        self._last()
        self.home()

    def _last(self, datamaster=None):
        # filters 最后一次交付内容的机会
        ret = 0
        for ff, fargs, fkwargs in self._ffilters:
            ret += ff.last(self, *fargs, **fkwargs)

        doticks = False
        if datamaster is not None and self._barstack:
            doticks = True

        while self._fromstack(forward=True):
            # 消费由 "last" 产生的 bar，并腾出空间
            pass

        if doticks:
            self._tick_fill()

        return bool(ret)

    def _check(self, forcedata=None):
        ret = 0
        for ff, fargs, fkwargs in self._filters:
            if not hasattr(ff, 'check'):
                continue
            ff.check(self, _forcedata=forcedata, *fargs, **fkwargs)

    def load(self):
        while True:
            # 为 new bar 将 data pointer 向前移动
            self.forward()

            if self._fromstack():  # bar is available
                return True

            if not self._fromstack(stash=True):
                _loadret = self._load()
                if not _loadret:  # 无 bar 时使用 force，确保 exactbars 场景正确
                    # 撤销 pointer，尤其覆盖已经看到最后一根 bar 的情况。
                    # 此时普通 backwards 会破坏 strategy "stop" 方法中的 pointer 记账。
                    self.backwards(force=True)  # 撤销 data pointer

                    # 返回实际返回值：None 表示当前无 bar 可用但 data feed 尚未结束；
                    # False 表示彻底结束。
                    return _loadret

            # 获取当前 loaded time 的引用
            dt = self.lines.datetime[0]

            # bar 已加载，适配时间
            if self._tzinput:
                # input stream 中的时间按表面值转换，但它并不是 UTC
                dtime = num2date(dt)  # 转为 naive datetime
                # localize
                dtime = self._tzinput.localize(dtime)  # pytz compatible-ized
                self.lines.datetime[0] = dt = date2num(dtime)  # keep UTC val

            # 检查标准 from/to date filter
            if dt < self.fromdate:
                # 丢弃 loaded bar 并继续
                self.backwards()
                continue
            if dt > self.todate:
                # 丢弃 loaded bar 并退出
                self.backwards(force=True)
                break

            # 通过 filters
            retff = False
            for ff, fargs, fkwargs in self._filters:
                # 前一个 filter 可能已把内容放入 stack
                if self._barstack:
                    for i in range(len(self._barstack)):
                        self._fromstack(forward=True)
                        retff = ff(self, *fargs, **fkwargs)
                else:
                    retff = ff(self, *fargs, **fkwargs)

                if retff:  # bar 已从系统中移除
                    break  # 跳出内层 loop

            if retff:  # bar 已从系统中移除，继续外层 loop 获取 new bar
                continue

            # checks 允许 bar 通过，通知调用方
            return True

        # 跳出 loop，表示无更多 bar 或已超过 todate
        return False

    def _load(self):
        return False

    def _add2stack(self, bar, stash=False):
        '''将给定 bar（value list）保存到 stack，供之后取回。'''
        if not stash:
            self._barstack.append(bar)
        else:
            self._barstash.append(bar)

    def _save2stack(self, erase=False, force=False, stash=False):
        '''将当前 bar 保存到 bar stack，供之后取回。

        Args:
            erase: 是否从 data stream 中移除当前 bar。
            force: 移除时是否强制回退 pointer。
            stash: 是否保存到 stash stack。
        '''
        bar = [line[0] for line in self.itersize()]
        if not stash:
            self._barstack.append(bar)
        else:
            self._barstash.append(bar)

        if erase:  # 按请求移除 bar
            self.backwards(force=force)

    def _updatebar(self, bar, forward=False, ago=0):
        '''把 stack 中的 value 加载到 lines，以形成 new bar。

        Args:
            bar: 要写入 line 的 value list。
            forward: 写入前是否先 forward。
            ago: 写入位置相对当前 bar 的偏移。
        '''
        if forward:
            self.forward()

        for line, val in zip(self.itersize(), bar):
            line[0 + ago] = val

    def _fromstack(self, forward=False, stash=False):
        '''从 stack 取出 value 并加载到 lines，以形成 new bar。

        Args:
            forward: 写入前是否先 forward。
            stash: 是否从 stash stack 读取。

        Returns:
            bool: stack 中有 value 并成功加载时返回 ``True``，否则返回 ``False``。
        '''

        coll = self._barstack if not stash else self._barstash

        if coll:
            if forward:
                self.forward()

            for line, val in zip(self.itersize(), coll.popleft()):
                line[0] = val

            return True

        return False

    def resample(self, **kwargs):
        self.addfilter(Resampler, **kwargs)

    def replay(self, **kwargs):
        self.addfilter(Replayer, **kwargs)


class DataBase(AbstractDataBase):
    '''DataBase 的基类，用于作为所有具体 data feed 的共同父类。'''
    pass


class FeedBase(with_metaclass(metabase.MetaParams, object)):
    '''Feed 的基类，用于管理多个 data feed 实例的创建、启动和停止。'''

    params = () + DataBase.params._gettuple()

    def __init__(self):
        self.datas = list()

    def start(self):
        for data in self.datas:
            data.start()

    def stop(self):
        for data in self.datas:
            data.stop()

    def getdata(self, dataname, name=None, **kwargs):
        for pname, pvalue in self.p._getitems():
            kwargs.setdefault(pname, getattr(self.p, pname))

        kwargs['dataname'] = dataname
        data = self._getdata(**kwargs)

        data._name = name

        self.datas.append(data)
        return data

    def _getdata(self, dataname, **kwargs):
        for pname, pvalue in self.p._getitems():
            kwargs.setdefault(pname, getattr(self.p, pname))

        kwargs['dataname'] = dataname
        return self.DataCls(**kwargs)


class MetaCSVDataBase(DataBase.__class__):
    '''CSV data feed metaclass 的基类，用于从文件名推导默认 data 名称。'''

    def dopostinit(cls, _obj, *args, **kwargs):
        # 先于 base class 处理，确保覆盖默认值
        if not _obj.p.name and not _obj._name:
            _obj._name, _ = os.path.splitext(os.path.basename(_obj.p.dataname))

        _obj, args, kwargs = \
            super(MetaCSVDataBase, cls).dopostinit(_obj, *args, **kwargs)

        return _obj, args, kwargs


class CSVDataBase(with_metaclass(MetaCSVDataBase, DataBase)):
    '''CSV DataFeed 的基类。

    该类负责打开文件、逐行读取并按 separator 切分 token。

    子类通常只需要覆盖：

      - ``_loadline(tokens)``

    ``_loadline`` 的返回值（``True``/``False``）会作为本基类覆盖的 ``_load`` 返回值。

    Args:
        headers: CSV 是否包含表头；默认 ``True`` 时启动阶段跳过第一行。
        separator: CSV 字段分隔符。

    Returns:
        CSVDataBase: 可由具体 CSV feed 继承的 data feed 基类。
    '''

    f = None
    params = (('headers', True), ('separator', ','),)

    def start(self):
        super(CSVDataBase, self).start()

        if self.f is None:
            if hasattr(self.p.dataname, 'readline'):
                self.f = self.p.dataname
            else:
                # 允许异常向上传播，让调用方知道打开失败
                self.f = io.open(self.p.dataname, 'r')

        if self.p.headers:
            self.f.readline()  # 跳过 header

        self.separator = self.p.separator

    def stop(self):
        super(CSVDataBase, self).stop()
        if self.f is not None:
            self.f.close()
            self.f = None

    def preload(self):
        while self.load():
            pass

        self._last()
        self.home()

        # 已 preload，无需继续持有文件对象；在 3.x 中会破坏 multiprocessing
        self.f.close()
        self.f = None

    def _load(self):
        if self.f is None:
            return False

        # 允许异常向上传播，让调用方知道读取失败
        line = self.f.readline()

        if not line:
            return False

        line = line.rstrip('\n')
        linetokens = line.split(self.separator)
        return self._loadline(linetokens)

    def _getnextline(self):
        if self.f is None:
            return None

        # 允许异常向上传播，让调用方知道读取失败
        line = self.f.readline()

        if not line:
            return None

        line = line.rstrip('\n')
        linetokens = line.split(self.separator)
        return linetokens


class CSVFeedBase(FeedBase):
    '''CSV Feed 的基类，用于按 basepath 创建 CSVDataBase 子类实例。'''

    params = (('basepath', ''),) + CSVDataBase.params._gettuple()

    def _getdata(self, dataname, **kwargs):
        return self.DataCls(dataname=self.p.basepath + dataname,
                            **self.p._getkwargs())


class DataClone(AbstractDataBase):
    '''data clone 的基类，用于复用另一个 data feed 的 line 和时间范围信息。'''

    _clone = True

    def __init__(self):
        self.data = self.p.dataname
        self._dataname = self.data._dataname

        # 复制 date/session 参数
        self.p.fromdate = self.p.fromdate
        self.p.todate = self.p.todate
        self.p.sessionstart = self.data.p.sessionstart
        self.p.sessionend = self.data.p.sessionend

        self.p.timeframe = self.data.p.timeframe
        self.p.compression = self.data.p.compression

    def _start(self):
        # 重新定义，用于从 guest data 复制 data bits
        self.start()

        # 复制 tz 信息
        self._tz = self.data._tz
        self.lines.datetime._settz(self._tz)

        self._calendar = self.data._calendar

        # input 已由 guest data 转换
        self._tzinput = None  # 无需进一步转换

        # 复制 dates/session 信息
        self.fromdate = self.data.fromdate
        self.todate = self.data.todate

        # FIXME: if removed from guest, remove here too
        self.sessionstart = self.data.sessionstart
        self.sessionend = self.data.sessionend

    def start(self):
        super(DataClone, self).start()
        self._dlen = 0
        self._preloading = False

    def preload(self):
        self._preloading = True
        super(DataClone, self).preload()
        self.data.home()  # preload 时 data 已被向前推进
        self._preloading = False

    def _load(self):
        # 假设 data 已在系统中，直接复制 lines
        if self._preloading:
            # data 已 preload，本 clone 也在 preload；可持续向前移动，
            # 直到得到完整 bar 或 data source 耗尽。
            self.data.advance()
            if len(self.data) > self.data.buflen():
                return False

            for line, dline in zip(self.lines, self.data.lines):
                line[0] = dline[0]

            return True

        # 非 preload 模式
        if not (len(self.data) > self._dlen):
            # Data 尚未超过上次看到的 bar
            return False

        self._dlen += 1

        for line, dline in zip(self.lines, self.data.lines):
            line[0] = dline[0]

        return True

    def advance(self, size=1, datamaster=None, ticks=True):
        self._dlen += size
        super(DataClone, self).advance(size, datamaster, ticks=ticks)

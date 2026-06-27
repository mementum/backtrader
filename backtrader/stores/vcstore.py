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
from datetime import date, datetime, time, timedelta
import os.path
import threading
import time as _timemod

import ctypes

from backtrader import TimeFrame, Position
from backtrader.feed import DataBase
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import (MAXINT, range, queue, string_types,
                                  with_metaclass)
from backtrader.utils import AutoDict


class _SymInfo(object):
    # SymbolInfo COM 对象副本，用于跨线程传递
    _fields = ['Type', 'Description', 'Decimals', 'TimeOffset',
               'PointValue', 'MinMovement']

    def __init__(self, syminfo):
        for f in self._fields:
            setattr(self, f, getattr(syminfo, f))

# 该类型在 'PumpEvents' 内使用；如果每次调用都重新创建，会为每次调用制造循环垃圾。
# 因此在这里统一定义。
_handles_type = ctypes.c_void_p * 1


def PumpEvents(timeout=-1, hevt=None, cb=None):
    """按 COM 需要的方式等待 ``timeout`` 秒。

    内部会根据当前线程所属 COM apartment 执行相应处理。按 CTRL+C 可终止 message
    loop，并抛出 KeyboardInterrupt。

    Args:
        timeout: 等待秒数，或返回等待秒数的 callable；``-1`` 表示无限等待。
        hevt: 可选的 Windows event handle。
        cb: timeout 后可调用的 callback。
    """
    # XXX 是否应支持传入额外 event handle 来终止该函数？

    # XXX XXX XXX
    #
    # 可能存在对 CoWaitForMultipleHandles 的理解偏差。STA 是否需要 message loop？
    # 看起来是需要的。
    #
    # MSDN 说明：
    #
    # 如果调用方位于 single-thread apartment，CoWaitForMultipleHandles 会进入 COM
    # modal loop，线程的 message loop 会继续通过 thread message filter 分发消息。
    # 如果线程未注册 message filter，则使用默认 COM message processing。
    #
    # 如果调用线程位于 multithread apartment (MTA)，CoWaitForMultipleHandles 会调用
    # Win32 函数 MsgWaitForMultipleObjects。

    # Timeout 预期为秒数 float，需要 *1000 转为毫秒。
    # timeout = -1 -> INFINITE 0xFFFFFFFF；也可以是返回秒数的 callable。

    if hevt is None:
        hevt = ctypes.windll.kernel32.CreateEventA(None, True, False, None)

    handles = _handles_type(hevt)
    RPC_S_CALLPENDING = -2147417835

    # @ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
    def HandlerRoutine(dwCtrlType):
        if dwCtrlType == 0:  # CTRL+C
            ctypes.windll.kernel32.SetEvent(hevt)
            return 1
        return 0

    HandlerRoutine = (
        ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)(HandlerRoutine)
    )

    ctypes.windll.kernel32.SetConsoleCtrlHandler(HandlerRoutine, 1)
    while True:
        try:
            tmout = timeout()  # check if it's a callable
        except TypeError:
            tmout = timeout  # it seems to be a number

        if tmout > 0:
            tmout *= 1000
        tmout = int(tmout)

        try:
            res = ctypes.oledll.ole32.CoWaitForMultipleHandles(
                0,  # COWAIT_FLAGS
                int(tmout),  # dwtimeout
                len(handles),  # number of handles in handles
                handles,  # handles array
                # 指示哪个 handle 被触发的指针
                ctypes.byref(ctypes.c_ulong())
            )

        except WindowsError as details:
            if details.args[0] == RPC_S_CALLPENDING:  # timeout expired
                if cb is not None:
                    cb()

                continue

            else:
                ctypes.windll.kernel32.CloseHandle(hevt)
                ctypes.windll.kernel32.SetConsoleCtrlHandler(HandlerRoutine, 0)
                raise  # something else happened
        else:
            ctypes.windll.kernel32.CloseHandle(hevt)
            ctypes.windll.kernel32.SetConsoleCtrlHandler(HandlerRoutine, 0)
            raise KeyboardInterrupt

        # finally:
        # if False:
            # ctypes.windll.kernel32.CloseHandle(hevt)
            # ctypes.windll.kernel32.SetConsoleCtrlHandler(HandlerRoutine, 0)
            # break


class RTEventSink(object):
    def __init__(self, store):
        self.store = store
        self.vcrtmod = store.vcrtmod
        self.lastconn = None

    def OnNewTicks(self, ArrayTicks):
        pass

    def OnServerShutDown(self):
        self.store._vcrt_connection(self.store._RT_SHUTDOWN)

    def OnInternalEvent(self, p1, p2, p3):
        if p1 != 1:  # 看起来是 "Connection Event"
            return

        if p2 == self.lastconn:
            return  # 不重复通知

        self.lastconn = p2  # 保存新的通知代码

        # p2 应为 0（disconn）或 1（conn）
        self.store._vcrt_connection(self.store._RT_BASEMSG - p2)


class MetaSingleton(MetaParams):
    '''让带 metaclass 的类成为 singleton 的 metaclass。'''
    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


class VCStore(with_metaclass(MetaSingleton, object)):
    '''封装 VisualChart COM 连接的 singleton store。

    参数也可在使用该 store 的类中指定，例如 ``VCData`` 和 ``VCBroker``。

    '''
    BrokerCls = None  # broker class 会自动注册
    DataCls = None  # data class 会自动注册

    # 用于 openinterest 校正的 32 bit 最大无符号整数
    MAXUINT = 0xffffffff // 2

    # 至少减去 1 秒，否则内部转换可能有问题
    MAXDATE1 = datetime.max - timedelta(days=1, seconds=1)
    MAXDATE2 = datetime.max - timedelta(seconds=1)

    _RT_SHUTDOWN = -0xffff
    _RT_BASEMSG = -0xfff0
    _RT_DISCONNECTED = -0xfff0
    _RT_CONNECTED = -0xfff1
    _RT_LIVE = -0xfff2
    _RT_DELAYED = -0xfff3
    _RT_TYPELIB = -0xffe0
    _RT_TYPEOBJ = -0xffe1
    _RT_COMTYPES = -0xffe2

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''使用 args/kwargs 返回 ``DataCls`` 实例。'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''使用注册的 ``BrokerCls`` 与 args/kwargs 返回 broker。'''
        return cls.BrokerCls(*args, **kwargs)

    # 找到时用于解析 TypeLibs 的 DLL
    VC64_DLLS = ('VCDataSource64.dll', 'VCRealTimeLib64.dll',
                 'COMTraderInterfaces64.dll',)

    VC_DLLS = ('VCDataSource.dll', 'VCRealTimeLib.dll',
               'COMTraderInterfaces.dll',)

    # 已知 CLSID
    VC_TLIBS = (
        ['{EB2A77DC-A317-4160-8833-DECF16275A05}', 1, 0],  # vcdatasource64
        ['{86F1DB04-2591-4866-A361-BB053D77FA18}', 1, 0],  # vcrealtime64
        ['{20F8873C-35BE-4DB4-8C2A-0A8D40F8AEC3}', 1, 0],  # raderinterface64
    )

    VC_KEYNAME = r'SOFTWARE\VCG\Visual Chart 6\Config'
    VC_KEYVAL = 'Directory'
    VC_BINPATH = 'bin'

    def find_vchart(self):
        # 尝试在注册表中定位 VisualChart 安装目录。
        # 找不到时返回已知 typelibs clsid；找到时扫描目录定位 64/32 bit DLL 并返回路径。
        import _winreg  # keep import local to avoid breaking test cases

        vcdir = None

        # 在常见根键中搜索 Directory
        for rkey in (_winreg.HKEY_CURRENT_USER, _winreg.HKEY_LOCAL_MACHINE,):
            try:
                vckey = _winreg.OpenKey(rkey, self.VC_KEYNAME)
            except WindowsError as e:
                continue

            # 尝试读取键值
            try:
                vcdir, _ = _winreg.QueryValueEx(vckey, self.VC_KEYVAL)
            except WindowsError as e:
                continue
            else:
                break  # 找到 vcdir

        if vcdir is None:
            return self.VC_TLIBS  # 未找到目录，最后回退

        # DLL 位于 bin 目录
        vcbin = os.path.join(vcdir, self.VC_BINPATH)

        # 在找到的目录中搜索 3 个库（64/32 bit）
        for dlls in (self.VC64_DLLS, self.VC_DLLS,):
            dfound = []
            for dll in dlls:
                fpath = os.path.join(vcbin, dll)
                if not os.path.isfile(fpath):
                    break
                dfound.append(fpath)

            if len(dfound) == len(dlls):
                return dfound

        # 未找到全部 DLL，最后回退
        return self.VC_TLIBS

    def _load_comtypes(self):
        # 将 comtypes import 保持为局部操作，避免破坏测试用例
        try:
            import comtypes
            self.comtypes = comtypes

            from comtypes.client import CreateObject, GetEvents, GetModule
            self.CreateObject = CreateObject
            self.GetEvents = GetEvents
            self.GetModule = GetModule
        except ImportError:
            return False

        return True  # 通知 comtypes 已加载

    def __init__(self):
        self._connected = False  # module/object 是否已创建

        self.notifs = collections.deque()  # 保存待发送通知

        self.t_vcconn = None  # 控制连接状态

        # 保存 market data symbol 对应的队列
        self._dqs = collections.deque()
        self._qdatas = dict()
        self._tftable = dict()

        if not self._load_comtypes():
            txt = 'Failed to import comtypes'
            msg = self._RT_COMTYPES, txt
            self.put_notification(msg, *msg)
            return

        vctypelibs = self.find_vchart()
        # 尝试加载模块
        try:
            self.vcdsmod = self.GetModule(vctypelibs[0])
            self.vcrtmod = self.GetModule(vctypelibs[1])
            self.vcctmod = self.GetModule(vctypelibs[2])
        except WindowsError as e:
            self.vcdsmod = None
            self.vcrtmod = None
            self.vcctmod = None
            txt = 'Failed to Load COM TypeLib Modules {}'.format(e)
            msg = self._RT_TYPELIB, txt
            self.put_notification(msg, *msg)
            return

        # 尝试加载主对象
        try:
            self.vcds = self.CreateObject(self.vcdsmod.DataSourceManager)
            # self.vcrt = self.CreateObject(self.vcrtmod.RealTime)
            self.vcct = self.CreateObject(self.vcctmod.Trader)
        except WindowsError as e:
            txt = ('Failed to Load COM TypeLib Objects but the COM TypeLibs '
                   'have been loaded. If VisualChart has been recently '
                   'installed/updated, restarting Windows may be necessary '
                   'to register the Objects: {}'.format(e))
            msg = self._RT_TYPELIB, txt
            self.put_notification(msg, *msg)
            self.vcds = None
            self.vcrt = None
            self.vcct = None
            return

        self._connected = True

        # 为调试目的构建 VCRT Field_XX 映射表
        self.vcrtfields = dict()
        for name in dir(self.vcrtmod):
            if name.startswith('Field'):
                self.vcrtfields[getattr(self.vcrtmod, name)] = name

        # module 和 object 已可创建
        self._tftable = {
            TimeFrame.Ticks: (self.vcdsmod.CT_Ticks, 1),
            TimeFrame.MicroSeconds: (self.vcdsmod.CT_Ticks, 1),  # To Resample
            TimeFrame.Seconds: (self.vcdsmod.CT_Ticks, 1),  # To Resample
            TimeFrame.Minutes: (self.vcdsmod.CT_Minutes, 1),
            TimeFrame.Days: (self.vcdsmod.CT_Days, 1),
            TimeFrame.Weeks: (self.vcdsmod.CT_Weeks, 1),
            TimeFrame.Months: (self.vcdsmod.CT_Months, 1),
            TimeFrame.Years: (self.vcdsmod.CT_Months, 12),
        }

    def put_notification(self, msg, *args, **kwargs):
        self.notifs.append((msg, args, kwargs))

    def get_notifications(self):
        '''返回待处理的 "store" 通知。'''
        self.notifs.append(None)  # 标记当前通知结尾
        return [x for x in iter(self.notifs.popleft, None)]  # popleft 直到 None

    def start(self, data=None, broker=None):
        if not self._connected:
            return

        if self.t_vcconn is None:
            # 启动连接状态检查线程
            self.t_vcconn = t = threading.Thread(target=self._start_vcrt)
            t.daemon = True  # 不阻止整体退出
            t.start()

        if broker is not None:
            t = threading.Thread(target=self._t_broker, args=(broker,))
            t.daemon = True
            t.start()

    def stop(self):
        pass  # 无需操作

    def connected(self):
        return self._connected

    def _start_vcrt(self):
        # 使用 VCRealTime 监控连接状态
        self.comtypes.CoInitialize()  # 在另一个线程中运行
        vcrt = self.CreateObject(self.vcrtmod.RealTime)
        sink = RTEventSink(self)
        conn = self.GetEvents(vcrt, sink)
        PumpEvents()
        self.comtypes.CoUninitialize()

    def _vcrt_connection(self, status):
        if status == -0xffff:
            txt = 'VisualChart shutting down',
        # p2: 0 -> Disconnected / p2: 1 -> Reconnected
        elif status == -0xfff0:
            txt = 'VisualChart is Disconnected'
        elif status == -0xfff1:
            txt = 'VisualChart is Connected'
        else:
            txt = 'VisualChart unknown connection status '

        msg = txt, status
        self.put_notification(msg, *msg)

        for q in self._dqs:
            q.put(status)

    def _tf2ct(self, timeframe, compression):
        # 将 timeframe 转换为 VisualChart 已知 compression type
        timeframe, extracomp = self._tftable[timeframe]
        return timeframe, compression * extracomp

    def _ticking(self, timeframe):
        # 将 timeframe 转换为 VisualChart 已知 compression type
        vctimeframe, _ = self._tftable[timeframe]
        return vctimeframe == self.vcdsmod.CT_Ticks

    def _getq(self, data):
        q = queue.Queue()
        self._dqs.append(q)
        self._qdatas[q] = data
        return q

    def _delq(self, q):
        self._dqs.remove(q)
        self._qdatas.pop(q)

    def _rtdata(self, data, symbol):
        kwargs = dict(data=data, symbol=symbol)
        t = threading.Thread(target=self._t_rtdata, kwargs=kwargs)
        t.daemon = True
        t.start()

    # Broker 函数
    def _t_rtdata(self, data, symbol):
        self.comtypes.CoInitialize()  # 在另一个线程中运行
        vcrt = self.CreateObject(self.vcrtmod.RealTime)
        conn = self.GetEvents(vcrt, data)
        data._vcrt = vcrt
        vcrt.RequestSymbolFeed(symbol, False)  # 不设限制
        PumpEvents()
        del conn  # 确保事件连接释放
        self.comtypes.CoUninitialize()

    def _symboldata(self, symbol):

        # 假设已连接且 symbol 已找到
        self.vcds.ActiveEvents = 0
        # self.vcds.EventsType = self.vcdsmod.EF_Always

        serie = self.vcds.NewDataSerie(symbol,
                                       self.vcdsmod.CT_Days, 1,
                                       self.MAXDATE1, self.MAXDATE2)

        syminfo = _SymInfo(serie.GetSymbolInfo())
        self.vcds.DeleteDataSource(serie)
        return syminfo

    def _canceldirectdata(self, q):
        self._delq(q)

    def _directdata(self, data,
                    symbol, timeframe, compression, d1, d2=None,
                    historical=False):

        # 假设 data 已经检查 symbol 存在
        timeframe, compression = self._tf2ct(timeframe, compression)
        kwargs = locals().copy()  # 复制参数
        kwargs.pop('self')
        kwargs['q'] = q = self._getq(data)

        t = threading.Thread(target=self._t_directdata, kwargs=kwargs)
        t.daemon = True
        t.start()

        # 使用 queue 同步，直到 symbolinfo 已获取
        return q  # 告诉调用方从哪里接收历史数据

    def _t_directdata(self, data,
                      symbol, timeframe, compression, d1, d2, q,
                      historical):

        self.comtypes.CoInitialize()  # 启动 COM 线程
        vcds = self.CreateObject(self.vcdsmod.DataSourceManager)

        historical = historical or d2 is not None
        if not historical:
            vcds.ActiveEvents = 1
            vcds.EventsType = self.vcdsmod.EF_Always
        else:
            vcds.ActiveEvents = 0

        if d2 is not None:
            serie = vcds.NewDataSerie(symbol, timeframe, compression, d1, d2)
        else:
            serie = vcds.NewDataSerie(symbol, timeframe, compression, d1)

        data._setserie(serie)

        # bar 处理可以继续
        data.OnNewDataSerieBar(serie, forcepush=historical)
        if historical:  # push the last bar
            q.put(None)        # 标记传输结束
            dsconn = None
        else:
            dsconn = self.GetEvents(vcds, data)  # 最后连接事件
            pass

        # 在该线程中 pump events，并调用 ping
        PumpEvents(timeout=data._getpingtmout, cb=data.ping)
        if dsconn is not None:
            del dsconn  # 文档建议删除连接

        # 退出线程前删除 series
        vcds.DeleteDataSource(serie)
        self.comtypes.CoUninitialize()  # 终止 COM 线程

    # Broker 函数
    def _t_broker(self, broker):
        self.comtypes.CoInitialize()  # 在另一个线程中运行
        trader = self.CreateObject(self.vcctmod.Trader)
        conn = self.GetEvents(trader, broker(trader))
        PumpEvents()
        del conn  # 确保事件连接释放
        self.comtypes.CoUninitialize()

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

# 下方模块应/必须通过 __all__ 定义希望导出的对象，
# 或为私有 class/variable 添加 "_"（underscore）前缀。

import sys

import backtrader as bt
from backtrader.utils.py3 import with_metaclass


try:
    import talib
except ImportError:
    __all__ = []  # talib 不可用
else:
    import numpy as np  # talib 依赖
    import talib.abstract

    MA_Type = talib.MA_Type

    # 反转 TA_FUNC_FLAGS dict
    R_TA_FUNC_FLAGS = dict(
        zip(talib.abstract.TA_FUNC_FLAGS.values(),
            talib.abstract.TA_FUNC_FLAGS.keys()))

    FUNC_FLAGS_SAMESCALE = 16777216
    FUNC_FLAGS_UNSTABLE = 134217728
    FUNC_FLAGS_CANDLESTICK = 268435456

    R_TA_OUTPUT_FLAGS = dict(
        zip(talib.abstract.TA_OUTPUT_FLAGS.values(),
            talib.abstract.TA_OUTPUT_FLAGS.keys()))

    OUT_FLAGS_LINE = 1
    OUT_FLAGS_DOTTED = 2
    OUT_FLAGS_DASH = 4
    OUT_FLAGS_HISTO = 16
    OUT_FLAGS_UPPER = 2048
    OUT_FLAGS_LOWER = 4096

    # 将所有 indicator 生成为 subclass

    class _MetaTALibIndicator(bt.Indicator.__class__):
        '''TA-Lib indicator metaclass 的基类，用于完成 lookback 和函数绑定。'''

        _refname = '_taindcol'
        _taindcol = dict()

        _KNOWN_UNSTABLE = ['SAR']

        def dopostinit(cls, _obj, *args, **kwargs):
            # 调用 parent
            res = super(_MetaTALibIndicator, cls).dopostinit(_obj,
                                                             *args, **kwargs)
            _obj, args, kwargs = res

            # 通过 abstract interface 和 params 获取 minimum period
            _obj._tabstract.set_function_args(**_obj.p._getkwargs())
            _obj._lookback = lookback = _obj._tabstract.lookback + 1
            _obj.updateminperiod(lookback)
            if _obj._unstable:
                _obj._lookback = 0

            elif cls.__name__ in cls._KNOWN_UNSTABLE:
                _obj._lookback = 0

            cerebro = bt.metabase.findowner(_obj, bt.Cerebro)
            tafuncinfo = _obj._tabstract.info
            _obj._tafunc = getattr(talib, tafuncinfo['name'], None)
            return _obj, args, kwargs  # 返回 object 和 args

    class _TALibIndicator(with_metaclass(_MetaTALibIndicator, bt.Indicator)):
        '''TA-Lib indicator 的基类，用于动态生成对应 backtrader indicator。'''

        CANDLEOVER = 1.02  # 上方 2%
        CANDLEREF = 1  # Open, High, Low, Close (0, 1, 2, 3)

        @classmethod
        def _subclass(cls, name):
            '''按 TA-Lib 函数名动态创建 indicator subclass。'''

            # class 最终所在的 module（即当前 module）
            clsmodule = sys.modules[cls.__module__]

            # 创建 abstract interface 以获取 lines names
            _tabstract = talib.abstract.Function(name)

            # 从 func_flags 中得到的信息
            iscandle = False
            unstable = False

            # 准备 plotinfo
            plotinfo = dict()
            fflags = _tabstract.function_flags or []
            for fflag in fflags:
                rfflag = R_TA_FUNC_FLAGS[fflag]
                if rfflag == FUNC_FLAGS_SAMESCALE:
                    plotinfo['subplot'] = False
                elif rfflag == FUNC_FLAGS_UNSTABLE:
                    unstable = True
                elif rfflag == FUNC_FLAGS_CANDLESTICK:
                    plotinfo['subplot'] = False
                    plotinfo['plotlinelabels'] = True
                    iscandle = True

            # 准备 plotlines
            lines = _tabstract.output_names
            output_flags = _tabstract.output_flags
            plotlines = dict()
            samecolor = False
            for lname in lines:
                oflags = output_flags.get(lname, None)
                pline = dict()
                for oflag in oflags or []:
                    orflag = R_TA_OUTPUT_FLAGS[oflag]
                    if orflag & OUT_FLAGS_LINE:
                        if not iscandle:
                            pline['ls'] = '-'
                        else:
                            pline['_plotskip'] = True  # 不绘制 candles

                    elif orflag & OUT_FLAGS_DASH:
                        pline['ls'] = '--'
                    elif orflag & OUT_FLAGS_DOTTED:
                        pline['ls'] = ':'
                    elif orflag & OUT_FLAGS_HISTO:
                        pline['_method'] = 'bar'

                    if samecolor:
                        pline['_samecolor'] = True

                    if orflag & OUT_FLAGS_LOWER:
                        samecolor = False

                    elif orflag & OUT_FLAGS_UPPER:
                        samecolor = True  # last：loop 中的其它值已被处理

                if pline:  # dict 中已有内容
                    plotlines[lname] = pline

            if iscandle:
                # 当 indicator 输出为 candle 时绘制这条 line。
                # candle 的值（100）会用于在产生 candle 的 bar 最大值上方绘制标记。
                pline = dict()
                pline['_name'] = name  # 绘制名称
                lname = '_candleplot'  # 修改名称
                lines.append(lname)
                pline['ls'] = ''
                pline['marker'] = 'd'
                pline['markersize'] = '7.0'
                pline['fillstyle'] = 'full'
                plotlines[lname] = pline

            # 准备用于 subclassing 的 dictionary
            clsdict = {
                '__module__': cls.__module__,
                '__doc__': str(_tabstract),
                '_tabstract': _tabstract,  # 保留引用，用于 lookback 计算
                '_iscandle': iscandle,
                '_unstable': unstable,
                'params': _tabstract.get_parameters(),
                'lines': tuple(lines),
                'plotinfo': plotinfo,
                'plotlines': plotlines,
            }
            newcls = type(str(name), (cls,), clsdict)  # subclass
            setattr(clsmodule, str(name), newcls)  # 添加到 module

        def oncestart(self, start, end):
            pass  # 否则 once 会收到单个 value 调用

        def once(self, start, end):
            import array

            # 准备 data arrays，一次性计算
            narrays = [np.array(x.lines[0].array) for x in self.datas]
            # 执行
            output = self._tafunc(*narrays, **self.p._getkwargs())

            fsize = self.size()
            lsize = fsize - self._iscandle
            if lsize == 1:  # 只有 1 个 output，不返回 tuple
                self.lines[0].array = array.array(str('d'), output)

                if fsize > lsize:  # 存在 candle
                    candleref = narrays[self.CANDLEREF] * self.CANDLEOVER
                    output2 = candleref * (output / 100.0)
                    self.lines[1].array = array.array(str('d'), output2)

            else:
                for i, o in enumerate(output):
                    self.lines[i].array = array.array(str('d'), o)

        def next(self):
            # 准备 data arrays，一次性计算
            size = self._lookback or len(self)
            narrays = [np.array(x.lines[0].get(size=size)) for x in self.datas]

            out = self._tafunc(*narrays, **self.p._getkwargs())

            fsize = self.size()
            lsize = fsize - self._iscandle
            if lsize == 1:  # 只有 1 个 output，不返回 tuple
                self.lines[0][0] = o = out[-1]

                if fsize > lsize:  # 存在 candle
                    candleref = narrays[self.CANDLEREF][-1] * self.CANDLEOVER
                    o2 = candleref * (o / 100.0)
                    self.lines[1][0] = o2

            else:
                for i, o in enumerate(out):
                    self.lines[i][0] = o[-1]

    # import module 时自动声明所有 TA-Lib 函数对应的 indicator
    tafunctions = talib.get_functions()
    for tafunc in tafunctions:
        _TALibIndicator._subclass(tafunc)

    __all__ = tafunctions + ['MA_Type', '_TALibIndicator']

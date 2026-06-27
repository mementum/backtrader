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
import io
import itertools
import sys

try:  # 新 Python 版本
    collectionsAbc = collections.abc  # collections.Iterable -> collections.abc.Iterable
except AttributeError:  # 旧 Python 版本
    collectionsAbc = collections  # 使用 collections.Iterable

import backtrader as bt
from backtrader.utils.py3 import (map, with_metaclass, string_types,
                                  integer_types)


class WriterBase(with_metaclass(bt.MetaParams, object)):
    pass


class WriterFile(WriterBase):
    '''系统级 writer 类，用于输出运行信息和可选 csv 数据流。

    Args:
      - ``out`` (default: ``sys.stdout``): 要写入的输出流。

        如果传入字符串，会将该参数内容作为文件名使用。

        如果希望在 multiprocess optimization 时使用 ``sys.stdout``，请保持为
        ``None``；子进程会自动初始化 ``sys.stdout``。

      - ``close_out`` (default: ``False``): 当 ``out`` 是 stream 时，writer 是否
        需要显式关闭它。

      - ``csv`` (default: ``False``): 是否在执行期间把 data feeds、strategies、
        observers 和 indicators 的 csv stream 写入输出流。

        哪些对象实际进入 csv stream，可通过各对象的 ``csv`` 属性控制。默认情况下
        ``data feeds`` 和 ``observers`` 为 ``True``，``indicators`` 为 ``False``。

      - ``csv_filternan`` (default: ``True``): 是否从 csv stream 中清理 ``nan``，
        并替换为空字段。

      - ``csv_counter`` (default: ``True``): 是否保留并输出实际写出行数的计数器。

      - ``indent`` (default: ``2``): 每一层缩进使用的空格数。

      - ``separators`` (default: ``['=', '-', '+', '*', '.', '~', '"', '^',
        '#']``): section/subsection 分隔线使用的字符。

      - ``seplen`` (default: ``79``): 分隔线总长度，包含缩进。

      - ``rounding`` (default: ``None``): float 向下保留的小数位数；``None`` 表示
        不做 rounding。

    Returns:
      WriterFile: 可由 Cerebro 调用的 writer 实例。
    '''
    params = (
        ('out', None),
        ('close_out', False),

        ('csv', False),
        ('csvsep', ','),
        ('csv_filternan', True),
        ('csv_counter', True),

        ('indent', 2),
        ('separators', ['=', '-', '+', '*', '.', '~', '"', '^', '#']),
        ('seplen', 79),
        ('rounding', None),
    )

    def __init__(self):
        self._len = itertools.count(1)
        self.headers = list()
        self.values = list()

    def _start_output(self):
        # 按需打开文件
        if not hasattr(self, 'out') or not self.out:
            if self.p.out is None:
                self.out = sys.stdout
                self.close_out = False
            elif isinstance(self.p.out, string_types):
                self.out = open(self.p.out, 'w')
                self.close_out = True
            else:
                self.out = self.p.out
                self.close_out = self.p.close_out

    def start(self):
        self._start_output()

        if self.p.csv:
            self.writelineseparator()
            self.writeiterable(self.headers, counter='Id')

    def stop(self):
        if self.close_out:
            self.out.close()

    def next(self):
        if self.p.csv:
            self.writeiterable(self.values, func=str, counter=next(self._len))
            self.values = list()

    def addheaders(self, headers):
        if self.p.csv:
            self.headers.extend(headers)

    def addvalues(self, values):
        if self.p.csv:
            if self.p.csv_filternan:
                values = map(lambda x: x if x == x else '', values)
            self.values.extend(values)

    def writeiterable(self, iterable, func=None, counter=''):
        if self.p.csv_counter:
            iterable = itertools.chain([counter], iterable)

        if func is not None:
            iterable = map(lambda x: func(x), iterable)

        line = self.p.csvsep.join(iterable)
        self.writeline(line)

    def writeline(self, line):
        self.out.write(line + '\n')

    def writelines(self, lines):
        for l in lines:
            self.out.write(l + '\n')

    def writelineseparator(self, level=0):
        sepnum = level % len(self.p.separators)
        separator = self.p.separators[sepnum]

        line = ' ' * (level * self.p.indent)
        line += separator * (self.p.seplen - (level * self.p.indent))
        self.writeline(line)

    def writedict(self, dct, level=0, recurse=False):
        if not recurse:
            self.writelineseparator(level)

        indent0 = level * self.p.indent
        for key, val in dct.items():
            kline = ' ' * indent0
            if recurse:
                kline += '- '

            kline += str(key) + ':'

            try:
                sclass = issubclass(val, bt.LineSeries)
            except TypeError:
                sclass = False

            if sclass:
                kline += ' ' + val.__name__
                self.writeline(kline)
            elif isinstance(val, string_types):
                kline += ' ' + val
                self.writeline(kline)
            elif isinstance(val, integer_types):
                kline += ' ' + str(val)
                self.writeline(kline)
            elif isinstance(val, float):
                if self.p.rounding is not None:
                    val = round(val, self.p.rounding)
                kline += ' ' + str(val)
                self.writeline(kline)
            elif isinstance(val, dict):
                if recurse:
                    self.writelineseparator(level=level)
                self.writeline(kline)
                self.writedict(val, level=level + 1, recurse=True)
            elif isinstance(val, (list, tuple, collectionsAbc.Iterable)):  # 不同 Python 版本会调用不同实现
                line = ', '.join(map(str, val))
                self.writeline(kline + ' ' + line)
            else:
                kline += ' ' + str(val)
                self.writeline(kline)


class WriterStringIO(WriterFile):
    params = (('out', io.StringIO),)

    def __init__(self):
        super(WriterStringIO, self).__init__()

    def _start_output(self):
        super(WriterStringIO, self)._start_output()
        self.out = self.out()

    def stop(self):
        super(WriterStringIO, self).stop()
        # 将文件位置留在开头
        self.out.seek(0)

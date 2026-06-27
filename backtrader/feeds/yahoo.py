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
from datetime import date, datetime
import io
import itertools

from ..utils.py3 import (urlopen, urlquote, ProxyHandler, build_opener,
                         install_opener)

import backtrader as bt
from .. import feed
from ..utils import date2num


class YahooFinanceCSVData(feed.CSVDataBase):
    '''
    解析已经下载好的 Yahoo CSV data feed；本地生成但符合 Yahoo 格式的 CSV
    也可以使用。

    Args:
        dataname: 要解析的文件名，或已经打开的类文件对象。
        reverse: 是否反转本地文件顺序，默认 ``False``。通常认为本地保存的文件在下载
            阶段已经处理过顺序。
        adjclose: 是否使用经过分红/拆股调整的 close，并据此调整全部价格字段。
        adjvolume: ``adjclose`` 为 ``True`` 时，是否同步调整 ``volume``。
        round: 是否在调整 close 后按指定小数位四舍五入。
        roundvolume: 调整 volume 后保留的小数位数。
        decimals: 价格字段保留的小数位数。
        swapcloses: 是否交换 close 与 adjusted close。该参数保留用于兼容 Yahoo
            可能再次调整列顺序的情况。

    Returns:
        YahooFinanceCSVData: 可加入 Cerebro 的 Yahoo CSV 数据源实例。

    ---
    交互界面使用示范:

    >>> data = YahooFinanceCSVData(dataname='YHOO.csv', reverse=True)
    >>> data.p.reverse
    True
    '''
    lines = ('adjclose',)

    params = (
        ('reverse', False),
        ('adjclose', True),
        ('adjvolume', True),
        ('round', True),
        ('decimals', 2),
        ('roundvolume', False),
        ('swapcloses', False),
    )

    def start(self):
        super(YahooFinanceCSVData, self).start()

        if not self.params.reverse:
            return

        # Yahoo 发送的数据是倒序，而文件还没有反转
        dq = collections.deque()
        for line in self.f:
            dq.appendleft(line)

        f = io.StringIO(newline=None)
        f.writelines(dq)
        f.seek(0)
        self.f.close()
        self.f = f

    def _loadline(self, linetokens):
        while True:
            nullseen = False
            for tok in linetokens[1:]:
                if tok == 'null':
                    nullseen = True
                    linetokens = self._getnextline()  # 重新获取 tokens
                    if not linetokens:
                        return False  # 无法继续获取，结束加载

                    # 跳出 for，继续 while True 的 null 检查逻辑
                    break

            if not nullseen:
                break  # 可以继续解析

        i = itertools.count(0)

        dttxt = linetokens[next(i)]
        dt = date(int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10]))
        dtnum = date2num(datetime.combine(dt, self.p.sessionend))

        self.lines.datetime[0] = dtnum
        o = float(linetokens[next(i)])
        h = float(linetokens[next(i)])
        l = float(linetokens[next(i)])
        c = float(linetokens[next(i)])
        self.lines.openinterest[0] = 0.0

        # 2018-11-16 起，Adjusted Close 看起来总是在 close 之后、volume 之前
        adjustedclose = float(linetokens[next(i)])
        try:
            v = float(linetokens[next(i)])
        except:  # 覆盖 volume 为 "null" 的情况
            v = 0.0

        if self.p.swapcloses:  # 按需交换 close 和 adjusted close
            c, adjustedclose = adjustedclose, c

        adjfactor = c / adjustedclose

        # v7 中似乎直接给出 adjusted prices，需要按比例还原未调整价格
        if self.params.adjclose:
            o /= adjfactor
            h /= adjfactor
            l /= adjfactor
            c = adjustedclose
            # 价格向下调整时，volume 要向上调整，反之亦然
            if self.p.adjvolume:
                v *= adjfactor

        if self.p.round:
            decimals = self.p.decimals
            o = round(o, decimals)
            h = round(h, decimals)
            l = round(l, decimals)
            c = round(c, decimals)

        v = round(v, self.p.roundvolume)

        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v
        self.lines.adjclose[0] = adjustedclose

        return True


class YahooLegacyCSV(YahooFinanceCSVData):
    '''
    用于加载 Yahoo 在 2017 年 5 月停用原始服务前下载的旧 CSV 文件。

    Args:
        version: 旧版兼容标记，默认空字符串。

    Returns:
        YahooLegacyCSV: 可加入 Cerebro 的旧版 Yahoo CSV 数据源实例。

    ---
    交互界面使用示范:

    >>> data = YahooLegacyCSV(dataname='legacy.csv')
    >>> data.p.version
    ''
    '''
    params = (
        ('version', ''),
    )


class YahooFinanceCSV(feed.CSVFeedBase):
    DataCls = YahooFinanceCSVData


class YahooFinanceData(YahooFinanceCSVData):
    '''
    按指定时间范围直接从 Yahoo 服务器下载数据。

    Args:
        dataname: 要下载的 ticker，例如 Yahoo 自身股票报价曾使用的 ``'YHOO'``。
        proxies: 下载时使用的代理字典，例如
            ``{'http': 'http://127.0.0.1:8080'}``。
        period: 下载周期，``'w'`` 表示周线，``'m'`` 表示月线。
        reverse: 在线下载默认返回正确顺序，因此默认为 ``False``。
        adjclose: 是否使用经过分红/拆股调整的 close，并据此调整全部价格字段。
        urlhist: Yahoo Finance 历史报价页面 URL，用于获取下载需要的 ``crumb`` cookie。
        urldown: 实际下载服务的 URL。
        retries: 获取 ``crumb`` 和下载数据各自最多重试的次数。

    Returns:
        YahooFinanceData: 可加入 Cerebro 的 Yahoo 在线数据源实例。

    ---
    交互界面使用示范:

    >>> data = YahooFinanceData(dataname='YHOO')
    >>> data.p.retries
    3
      '''

    params = (
        ('proxies', {}),
        ('period', 'd'),
        ('reverse', False),
        ('urlhist', 'https://finance.yahoo.com/quote/{}/history'),
        ('urldown', 'https://query1.finance.yahoo.com/v7/finance/download'),
        ('retries', 3),
    )

    def start_v7(self):
        try:
            import requests
        except ImportError:
            msg = ('The new Yahoo data feed requires to have the requests '
                   'module installed. Please use pip install requests or '
                   'the method of your choice')
            raise Exception(msg)

        self.error = None
        url = self.p.urlhist.format(self.p.dataname)

        sesskwargs = dict()
        if self.p.proxies:
            sesskwargs['proxies'] = self.p.proxies

        crumb = None
        sess = requests.Session()
        sess.headers['User-Agent'] = 'backtrader'
        for i in range(self.p.retries + 1):  # 至少尝试一次
            resp = sess.get(url, **sesskwargs)
            if resp.status_code != requests.codes.ok:
                continue

            txt = resp.text
            i = txt.find('CrumbStore')
            if i == -1:
                continue
            i = txt.find('crumb', i)
            if i == -1:
                continue
            istart = txt.find('"', i + len('crumb') + 1)
            if istart == -1:
                continue
            istart += 1
            iend = txt.find('"', istart)
            if iend == -1:
                continue

            crumb = txt[istart:iend]
            crumb = crumb.encode('ascii').decode('unicode-escape')
            break

        if crumb is None:
            self.error = 'Crumb not found'
            self.f = None
            return

        crumb = urlquote(crumb)

        # urldown/ticker?period1=posix1&period2=posix2&interval=1d&events=history&crumb=crumb

        # 尝试下载
        urld = '{}/{}'.format(self.p.urldown, self.p.dataname)

        urlargs = []
        posix = date(1970, 1, 1)
        if self.p.todate is not None:
            period2 = (self.p.todate.date() - posix).total_seconds()
            urlargs.append('period2={}'.format(int(period2)))

        if self.p.todate is not None:
            period1 = (self.p.fromdate.date() - posix).total_seconds()
            urlargs.append('period1={}'.format(int(period1)))

        intervals = {
            bt.TimeFrame.Days: '1d',
            bt.TimeFrame.Weeks: '1wk',
            bt.TimeFrame.Months: '1mo',
        }

        urlargs.append('interval={}'.format(intervals[self.p.timeframe]))
        urlargs.append('events=history')
        urlargs.append('crumb={}'.format(crumb))

        urld = '{}?{}'.format(urld, '&'.join(urlargs))
        f = None
        for i in range(self.p.retries + 1):  # 至少尝试一次
            resp = sess.get(urld, **sesskwargs)
            if resp.status_code != requests.codes.ok:
                continue

            ctype = resp.headers['Content-Type']
            # 尽量覆盖 Yahoo 可能返回的各种文本类型
            if not ctype.startswith('text/'):
                self.error = 'Wrong content type: %s' % ctype
                continue  # 返回了 HTML，通常表示 URL 不正确

            # 把 socket 返回内容全部缓冲到本地
            try:
                # r.encoding = 'UTF-8'
                f = io.StringIO(resp.text, newline=None)
            except Exception:
                continue  # 如果还能重试，则继续尝试

            break

        self.f = f

    def start(self):
        self.start_v7()

        # 已准备好类文件对象，交给 CSV parser 接管
        super(YahooFinanceData, self).start()


class YahooFinance(feed.CSVFeedBase):
    DataCls = YahooFinanceData

    params = DataCls.params._gettuple()

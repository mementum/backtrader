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

from .. import feed
from ..utils import date2num


__all__ = ['QuandlCSV', 'Quandl']


class QuandlCSV(feed.CSVDataBase):
    '''
    解析已经下载好的 Quandl CSV data feed；本地生成但符合 Quandl 格式的 CSV
    也可以使用。

    Args:
        dataname: 要解析的文件名，或已经打开的类文件对象。
        reverse: 是否反转本地文件顺序，默认 ``False``。通常认为本地保存的文件在下载
            阶段已经处理过顺序。
        adjclose: 是否使用经过分红/拆股调整的 close，并据此调整全部价格字段。
        round: 是否在调整 close 后按指定小数位四舍五入。
        decimals: ``round`` 启用时保留的小数位数。

    Returns:
        QuandlCSV: 可加入 Cerebro 的 Quandl CSV 数据源实例。

    ---
    交互界面使用示范:

    >>> data = QuandlCSV(dataname='WIKI-AAPL.csv', reverse=True)
    >>> data.p.reverse
    True
    '''
    _online = False  # 避免重复反转的标记

    params = (
        ('reverse', False),
        ('adjclose', True),
        ('round', False),
        ('decimals', 2),
    )

    def start(self):
        super(QuandlCSV, self).start()

        if not self.params.reverse:
            return
        elif self._online:
            return  # reverse 为 True 且在线下载时，已通过 order=asc 处理

        # Quandl 数据可能倒序排列，需要反转
        dq = collections.deque()
        for line in self.f:
            dq.appendleft(line)

        f = io.StringIO(newline=None)
        f.writelines(dq)
        f.seek(0)
        self.f.close()
        self.f = f

    def _loadline(self, linetokens):
        i = itertools.count(0)

        dttxt = linetokens[next(i)]  # YYYY-MM-DD 格式
        dt = date(int(dttxt[0:4]), int(dttxt[5:7]), int(dttxt[8:10]))
        dtnum = date2num(datetime.combine(dt, self.p.sessionend))

        self.lines.datetime[0] = dtnum
        if self.p.adjclose:
            for _ in range(7):
                next(i)  # 跳过 ohlcv、除息、拆股比例

        o = float(linetokens[next(i)])
        h = float(linetokens[next(i)])
        l = float(linetokens[next(i)])
        c = float(linetokens[next(i)])
        v = float(linetokens[next(i)])
        self.lines.openinterest[0] = 0.0

        if self.p.round:
            decimals = self.p.decimals
            o = round(o, decimals)
            h = round(h, decimals)
            l = round(l, decimals)
            c = round(c, decimals)
            v = round(v, decimals)

        self.lines.open[0] = o
        self.lines.high[0] = h
        self.lines.low[0] = l
        self.lines.close[0] = c
        self.lines.volume[0] = v

        return True


class Quandl(QuandlCSV):
    '''
    按指定时间范围直接从 Quandl 服务器下载数据。

    Args:
        dataname: 要下载的 ticker，例如 ``'YHOO'``。
        baseurl: 服务端 URL。未来也可以指向兼容 Quandl 格式的服务。
        proxies: 下载时使用的代理字典，例如
            ``{'http': 'http://127.0.0.1:8080'}``。
        buffered: 是否先把整个 socket 返回内容缓冲到本地，再开始解析。
        reverse: Quandl 默认返回倒序数据。为 ``True`` 时，请求会要求 Quandl 返回
            升序数据，也就是从旧到新。
        adjclose: 是否使用经过分红/拆股调整的 close，并据此调整全部价格字段。
        apikey: 需要时传入 Quandl API key。
        dataset: 要查询的数据集名称，默认 ``WIKI``。

    Returns:
        Quandl: 可加入 Cerebro 的 Quandl 在线数据源实例。

    ---
    交互界面使用示范:

    >>> data = Quandl(dataname='YHOO', dataset='WIKI')
    >>> data.p.dataset
    'WIKI'
      '''

    _online = True  # 避免重复反转的标记

    params = (
        ('baseurl', 'https://www.quandl.com/api/v3/datasets'),
        ('proxies', {}),
        ('buffered', True),
        ('reverse', True),
        ('apikey', None),
        ('dataset', 'WIKI'),
    )

    def start(self):
        self.error = None

        url = '{}/{}/{}.csv'.format(
            self.p.baseurl, self.p.dataset, urlquote(self.p.dataname))

        urlargs = []
        if self.p.reverse:
            urlargs.append('order=asc')

        if self.p.apikey is not None:
            urlargs.append('api_key={}'.format(self.p.apikey))

        if self.p.fromdate:
            dtxt = self.p.fromdate.strftime('%Y-%m-%d')
            urlargs.append('start_date={}'.format(dtxt))

        if self.p.todate:
            dtxt = self.p.todate.strftime('%Y-%m-%d')
            urlargs.append('end_date={}'.format(dtxt))

        if urlargs:
            url += '?' + '&'.join(urlargs)

        if self.p.proxies:
            proxy = ProxyHandler(self.p.proxies)
            opener = build_opener(proxy)
            install_opener(opener)

        try:
            datafile = urlopen(url)
        except IOError as e:
            self.error = str(e)
            # 保持空数据源
            return

        if datafile.headers['Content-Type'] != 'text/csv':
            self.error = 'Wrong content type: %s' % datafile.headers
            return  # 返回了 HTML，通常表示 URL 不正确

        if self.params.buffered:
            # 把 socket 返回内容全部缓冲到本地
            f = io.StringIO(datafile.read().decode('utf-8'), newline=None)
            datafile.close()
        else:
            f = datafile

        self.f = f

        # 已准备好类文件对象，交给 CSV parser 接管
        super(Quandl, self).start()

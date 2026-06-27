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

import math

from backtrader.utils.py3 import itervalues

from backtrader import Analyzer, TimeFrame
from backtrader.mathsupport import average, standarddev
from backtrader.analyzers import TimeReturn, AnnualReturn


class SharpeRatio(Analyzer):
    '''使用 risk-free rate 计算 strategy Sharpe Ratio 的 analyzer。

    See also:

      - https://en.wikipedia.org/wiki/Sharpe_ratio

    Args:
        timeframe: 统计使用的 timeframe，默认 ``TimeFrame.Years``。
        compression (int): timeframe 压缩倍数，默认 ``1``。仅用于日内
            timeframe。
        riskfreerate (float): 年化 risk-free rate，默认 ``0.01``（1%）。
        factor: annual risk-free rate 到所选 timeframe 的转换因子，默认
            ``None``。如果为 ``None``，会从预设表中选择:
            Days=252、Weeks=52、Months=12、Years=1。
        convertrate (bool): 是否将 ``riskfreerate`` 从年化转换为月/周/日
            rate，默认 ``True``。不支持日内转换。
        annualize (bool): 是否返回年化 Sharpe Ratio，默认 ``False``。
        stddev_sample (bool): 是否使用样本标准差，默认 ``False``。设为
            ``True`` 时使用 Bessel's correction。
        daysfactor: ``factor`` 的旧名称，默认 ``None``。如果 timeframe 是
            ``TimeFrame.Days`` 且该参数不为 ``None``，会按旧代码行为使用它。
        legacyannual (bool): 是否使用 ``AnnualReturn`` analyzer，默认
            ``False``。该 analyzer 只按年份工作。
        fund: 如果为 ``None``，会自动检测 broker 的实际模式（fundmode -
            True/False），以决定 returns 基于总净资产 value 还是 fund value。
            将其设为 ``True`` 或 ``False`` 可指定具体行为。

    Returns:
        dict: ``get_analysis`` 返回包含 ``sharperatio`` key 的字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(SharpeRatio, _name='sharpe')

    '''
    params = (
        ('timeframe', TimeFrame.Years),
        ('compression', 1),
        ('riskfreerate', 0.01),
        ('factor', None),
        ('convertrate', True),
        ('annualize', False),
        ('stddev_sample', False),

        # 旧行为
        ('daysfactor', None),
        ('legacyannual', False),
        ('fund', None),
    )

    RATEFACTORS = {
        TimeFrame.Days: 252,
        TimeFrame.Weeks: 52,
        TimeFrame.Months: 12,
        TimeFrame.Years: 1,
    }

    def __init__(self):
        if self.p.legacyannual:
            self.anret = AnnualReturn()
        else:
            self.timereturn = TimeReturn(
                timeframe=self.p.timeframe,
                compression=self.p.compression,
                fund=self.p.fund)

    def stop(self):
        super(SharpeRatio, self).stop()
        if self.p.legacyannual:
            rate = self.p.riskfreerate
            retavg = average([r - rate for r in self.anret.rets])
            retdev = standarddev(self.anret.rets)

            self.ratio = retavg / retdev
        else:
            # 从子 analyzer 获取 returns
            returns = list(itervalues(self.timereturn.get_analysis()))

            rate = self.p.riskfreerate  #

            factor = None

            # 用于识别旧代码的兼容逻辑
            if self.p.timeframe == TimeFrame.Days and \
               self.p.daysfactor is not None:

                factor = self.p.daysfactor

            else:
                if self.p.factor is not None:
                    factor = self.p.factor  # 用户指定的 factor
                elif self.p.timeframe in self.RATEFACTORS:
                    # 从默认表中获取转换 factor
                    factor = self.RATEFACTORS[self.p.timeframe]

            if factor is not None:
                # 找到 factor

                if self.p.convertrate:
                    # 标准做法：将年化 return 降频到 timeframe factor
                    rate = pow(1.0 + rate, 1.0 / factor) - 1.0
                else:
                    # 否则将 returns 升频到年度 returns
                    returns = [pow(1.0 + x, factor) - 1.0 for x in returns]

            lrets = len(returns) - self.p.stddev_sample
            # 检查 ratio 是否可计算
            if lrets:
                # 计算 excess returns、算术平均和原始 sharpe
                ret_free = [r - rate for r in returns]
                ret_free_avg = average(ret_free)
                retdev = standarddev(ret_free, avgx=ret_free_avg,
                                     bessel=self.p.stddev_sample)

                try:
                    ratio = ret_free_avg / retdev

                    if factor is not None and \
                       self.p.convertrate and self.p.annualize:

                        ratio = math.sqrt(factor) * ratio
                except (ValueError, TypeError, ZeroDivisionError):
                    ratio = None
            else:
                # 无 returns，或 stddev_sample 启用且只有 1 个 return
                ratio = None

            self.ratio = ratio

        self.rets['sharperatio'] = self.ratio


class SharpeRatio_A(SharpeRatio):
    '''直接返回年化 Sharpe Ratio 的 ``SharpeRatio`` 扩展类。

    Args:
        annualize (bool): 默认改为 ``True``。

    Returns:
        dict: ``get_analysis`` 返回包含 ``sharperatio`` key 的字典。

    ---
    >>> import backtrader as bt
    >>> cerebro = bt.Cerebro()
    >>> cerebro.addanalyzer(SharpeRatio_A, _name='sharpe_annual')

    '''

    params = (
        ('annualize', True),
    )

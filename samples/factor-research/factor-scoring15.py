#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# 因子研究第 15 课：四因子截面预处理
#
# 目标：
#   1. 把价值、质量、动量、低风险统一为“越高越好”
#   2. 用 MAD 缩尾限制极端值
#   3. 对行业和对数市值做线性中性化
#   4. 标准化后等权合成
#
# 这是单个调仓日的截面实验。输入可替换为任何具有相同字段的 CSV。
###############################################################################
from __future__ import absolute_import, division, print_function

import argparse
import math
import os

import numpy as np
import pandas as pd


FACTOR_SPECS = (
    ('value', 'earnings_yield', 1.0),
    ('quality', 'roe', 1.0),
    ('momentum', 'momentum_12_1', 1.0),
    ('low_risk', 'volatility_120', -1.0),
)
REQUIRED_COLUMNS = (
    'symbol', 'name', 'industry', 'market_cap',
    'earnings_yield', 'roe', 'momentum_12_1', 'volatility_120',
)


def mad_winsorize(series, limit=3.0):
    values = pd.to_numeric(series, errors='coerce')
    median = values.median()
    mad = (values - median).abs().median()
    scale = mad * 1.4826

    if not math.isfinite(scale) or scale < 1e-12:
        scale = values.std(ddof=0)
    if not math.isfinite(scale) or scale < 1e-12:
        return values.fillna(median)

    lower = median - limit * scale
    upper = median + limit * scale
    return values.clip(lower=lower, upper=upper)


def standardize(series):
    values = pd.to_numeric(series, errors='coerce')
    deviation = values.std(ddof=0)
    if not math.isfinite(deviation) or deviation < 1e-12:
        return pd.Series(0.0, index=series.index)
    return (values - values.mean()) / deviation


def build_controls(frame):
    industries = pd.get_dummies(
        frame['industry'], prefix='industry', drop_first=True, dtype=float)
    controls = pd.concat([
        pd.Series(1.0, index=frame.index, name='intercept'),
        np.log(frame['market_cap']).rename('log_market_cap'),
        industries,
    ], axis=1)
    return controls


def neutralize(series, controls):
    valid = series.notna() & controls.notna().all(axis=1)
    residuals = pd.Series(np.nan, index=series.index, dtype=float)
    if valid.sum() <= controls.shape[1]:
        raise ValueError('有效股票数量不足，无法完成行业与市值中性化')

    x_values = controls.loc[valid].to_numpy(dtype=float)
    y_values = series.loc[valid].to_numpy(dtype=float)
    coefficients = np.linalg.lstsq(x_values, y_values, rcond=None)[0]
    residuals.loc[valid] = y_values - x_values.dot(coefficients)
    return residuals


def validate_input(frame):
    missing = [column for column in REQUIRED_COLUMNS
               if column not in frame.columns]
    if missing:
        raise ValueError('输入缺少字段: {}'.format(', '.join(missing)))

    numeric = REQUIRED_COLUMNS[3:]
    frame = frame.copy()
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors='coerce')
    frame = frame.dropna(subset=list(REQUIRED_COLUMNS))

    if len(frame) < 10:
        raise ValueError('至少需要 10 只有效股票演示截面处理')
    if frame['industry'].nunique() < 2:
        raise ValueError('至少需要两个行业演示行业中性化')
    if (frame['market_cap'] <= 0).any():
        raise ValueError('market_cap 必须全部大于 0')
    return frame.reset_index(drop=True)


def score_factors(frame):
    result = validate_input(frame)
    controls = build_controls(result)
    result['naive_score'] = 0.0
    result['composite_score'] = 0.0

    for factor, source, direction in FACTOR_SPECS:
        directed = direction * result[source]
        winsorized = mad_winsorize(directed)
        result[factor + '_winsorized'] = winsorized
        result[factor + '_naive_z'] = standardize(winsorized)

        residual = neutralize(winsorized, controls)
        result[factor + '_neutral'] = residual
        result[factor + '_z'] = standardize(residual)

        result['naive_score'] += 0.25 * result[factor + '_naive_z']
        result['composite_score'] += 0.25 * result[factor + '_z']

    result['naive_rank'] = result['naive_score'].rank(
        ascending=False, method='min').astype(int)
    result['final_rank'] = result['composite_score'].rank(
        ascending=False, method='min').astype(int)
    result['rank_change'] = result['naive_rank'] - result['final_rank']
    return result.sort_values('final_rank')


def print_rankings(scored, top):
    display_columns = [
        'final_rank', 'symbol', 'name', 'industry', 'market_cap',
        'value_z', 'quality_z', 'momentum_z', 'low_risk_z',
        'composite_score', 'naive_rank', 'rank_change',
    ]
    view = scored[display_columns].head(top).copy()
    print('\n中性化后的 Top {}'.format(min(top, len(view))))
    print('-' * 116)
    print(view.to_string(index=False, formatters={
        'market_cap': '{:.0f}'.format,
        'value_z': '{:+.2f}'.format,
        'quality_z': '{:+.2f}'.format,
        'momentum_z': '{:+.2f}'.format,
        'low_risk_z': '{:+.2f}'.format,
        'composite_score': '{:+.3f}'.format,
        'rank_change': '{:+d}'.format,
    }))

    naive = scored.sort_values('naive_rank').head(top)
    print('\n未中性化的 Top {}'.format(min(top, len(naive))))
    print('-' * 78)
    print(naive[[
        'naive_rank', 'symbol', 'name', 'industry',
        'market_cap', 'naive_score', 'final_rank',
    ]].to_string(index=False, formatters={
        'market_cap': '{:.0f}'.format,
        'naive_score': '{:+.3f}'.format,
    }))


def print_diagnostics(scored):
    print('\n中性化诊断')
    print('-' * 78)
    log_size = np.log(scored['market_cap'])
    for factor, _, _ in FACTOR_SPECS:
        residual = scored[factor + '_neutral']
        size_correlation = residual.corr(log_size)
        industry_means = scored.groupby(
            'industry')[factor + '_neutral'].mean()
        print(
            '{:<10} 市值相关={:+.6f}  最大行业均值绝对值={:.6f}'.format(
                factor,
                size_correlation,
                industry_means.abs().max()))


def parse_args(pargs=None):
    default_input = os.path.join(
        os.path.dirname(__file__), 'factor-scoring15-input.csv')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='四因子截面处理：缩尾、中性化、标准化和等权合成')
    parser.add_argument('--input', default=default_input)
    parser.add_argument('--output', default='',
                        help='可选：保存完整因子明细 CSV')
    parser.add_argument('--top', type=int, default=8)
    return parser.parse_args(pargs)


def run(pargs=None):
    args = parse_args(pargs)
    frame = pd.read_csv(args.input, dtype={'symbol': str})
    scored = score_factors(frame)

    print('=' * 116)
    print('四因子截面打分')
    print('方向: 价值↑ 质量↑ 动量↑ 波动率↓')
    print('处理: MAD 缩尾 -> 行业与对数市值中性化 -> Z-score -> 等权合成')
    print('=' * 116)
    print_rankings(scored, args.top)
    print_diagnostics(scored)

    if args.output:
        output = os.path.abspath(args.output)
        parent = os.path.dirname(output)
        if parent:
            os.makedirs(parent, exist_ok=True)
        scored.to_csv(output, index=False)
        print('\n完整明细已写入 {}'.format(output))
    return scored


if __name__ == '__main__':
    run()

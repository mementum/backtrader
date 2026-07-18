#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# 因子研究第 16 课：月度四因子面板
#
# 本脚本用固定随机种子生成教学数据，目标是验证研究流程，而不是证明真实
# A 股因子有效。每个月先调用第 15 课的截面处理，再生成下一持有期收益。
# 真实研究时，只需把 build_teaching_panel 替换成 point-in-time 数据读取。
###############################################################################
from __future__ import absolute_import, division, print_function

import argparse
import importlib.util
import math
import os

import numpy as np
import pandas as pd


FACTOR_NAMES = ('value', 'quality', 'momentum', 'low_risk')
FACTOR_COLUMNS = tuple(name + '_z' for name in FACTOR_NAMES)
SIGNAL_COLUMNS = FACTOR_COLUMNS + ('composite_score',)


def load_scoring_lesson():
    path = os.path.join(os.path.dirname(__file__), 'factor-scoring15.py')
    spec = importlib.util.spec_from_file_location('factor_scoring15', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCORING = load_scoring_lesson()


def initialize_states(base):
    return {
        'log_market_cap': np.log(base['market_cap'].to_numpy(dtype=float)),
        'log_earnings_yield': np.log(
            base['earnings_yield'].to_numpy(dtype=float)),
        'roe': base['roe'].to_numpy(dtype=float),
        'momentum': base['momentum_12_1'].to_numpy(dtype=float),
        'volatility': base['volatility_120'].to_numpy(dtype=float),
    }


def evolve_cross_section(base, states, rng):
    count = len(base)
    states['log_market_cap'] += rng.normal(0.005, 0.045, count)
    states['log_earnings_yield'] = (
        0.88 * states['log_earnings_yield']
        + 0.12 * np.log(base['earnings_yield'].to_numpy(dtype=float))
        + rng.normal(0.0, 0.09, count))
    states['roe'] = (
        0.90 * states['roe']
        + 0.10 * base['roe'].to_numpy(dtype=float)
        + rng.normal(0.0, 0.018, count))
    states['momentum'] = (
        0.62 * states['momentum'] + rng.normal(0.0, 0.16, count))
    states['volatility'] = (
        0.82 * states['volatility']
        + 0.18 * base['volatility_120'].to_numpy(dtype=float)
        + rng.normal(0.0, 0.028, count))

    cross_section = base[['symbol', 'name', 'industry']].copy()
    cross_section['market_cap'] = np.exp(states['log_market_cap'])
    cross_section['earnings_yield'] = np.exp(
        states['log_earnings_yield']).clip(0.005, 0.30)
    cross_section['roe'] = np.clip(states['roe'], -0.10, 0.50)
    cross_section['momentum_12_1'] = np.clip(
        states['momentum'], -0.70, 1.20)
    cross_section['volatility_120'] = np.clip(
        states['volatility'], 0.08, 0.75)
    return cross_section


def simulated_premia(month_index, months):
    split_index = int(months * 0.75)
    if month_index < split_index:
        return 'development', {
            'value_z': 0.0060,
            'quality_z': 0.0050,
            'momentum_z': 0.0040,
            'low_risk_z': 0.0030,
        }
    return 'holdout', {
        'value_z': 0.0030,
        'quality_z': 0.0050,
        'momentum_z': -0.0035,
        'low_risk_z': 0.0020,
    }


def build_teaching_panel(base, start, months, seed):
    if months < 24:
        raise ValueError('至少需要 24 个月，才能演示样本切分')

    base = SCORING.validate_input(base)
    rng = np.random.default_rng(seed)
    states = initialize_states(base)
    dates = pd.date_range(start=start, periods=months, freq='ME')
    records = []

    for month_index, signal_date in enumerate(dates):
        raw = evolve_cross_section(base, states, rng)
        scored = SCORING.score_factors(raw)
        regime, premia = simulated_premia(month_index, months)

        market_return = rng.normal(0.004, 0.028)
        alpha = sum(
            coefficient * scored[column]
            for column, coefficient in premia.items())
        future_return = market_return + alpha + rng.normal(
            0.0, 0.045, len(scored))

        scored['signal_date'] = signal_date
        scored['entry_date'] = signal_date + pd.offsets.BDay(1)
        scored['exit_date'] = (
            signal_date + pd.offsets.MonthEnd(1) + pd.offsets.BDay(1))
        scored['future_return'] = future_return
        scored['regime'] = regime
        records.append(scored)

    panel = pd.concat(records, ignore_index=True)
    return panel.set_index(['signal_date', 'symbol']).sort_index()


def audit_panel(panel):
    if panel.index.duplicated().any():
        raise ValueError('面板存在重复的 signal_date + symbol')
    if panel[list(SIGNAL_COLUMNS) + ['future_return']].isna().any().any():
        raise ValueError('面板存在缺失的因子分或未来收益')

    counts = panel.groupby(level='signal_date').size()
    if counts.nunique() != 1:
        raise ValueError('教学面板每个月的股票数应保持一致')

    maximum_mean = 0.0
    maximum_std_error = 0.0
    for _, section in panel.groupby(level='signal_date'):
        for column in FACTOR_COLUMNS:
            maximum_mean = max(maximum_mean, abs(section[column].mean()))
            maximum_std_error = max(
                maximum_std_error,
                abs(section[column].std(ddof=0) - 1.0))
    return {
        'months': panel.index.get_level_values('signal_date').nunique(),
        'assets_per_month': int(counts.iloc[0]),
        'maximum_factor_mean': maximum_mean,
        'maximum_factor_std_error': maximum_std_error,
    }


def information_coefficients(panel, signal_columns=SIGNAL_COLUMNS):
    rows = []
    for date, section in panel.groupby(level='signal_date'):
        future = section['future_return']
        for column in signal_columns:
            values = section[column]
            rows.append({
                'signal_date': date,
                'factor': column,
                'ic': values.corr(future, method='pearson'),
                'rank_ic': values.corr(future, method='spearman'),
                'assets': len(section),
            })
    return pd.DataFrame(rows)


def summarize_ic(ic_frame):
    rows = []
    for factor, values in ic_frame.groupby('factor', sort=False):
        values = values.dropna(subset=['ic', 'rank_ic'])
        rank_std = values['rank_ic'].std(ddof=1)
        rows.append({
            'factor': factor,
            'months': len(values),
            'mean_ic': values['ic'].mean(),
            'mean_rank_ic': values['rank_ic'].mean(),
            'rank_icir': (
                values['rank_ic'].mean() / rank_std * math.sqrt(12)
                if len(values) > 1 and rank_std > 0 else np.nan),
            'rank_positive': (values['rank_ic'] > 0).mean(),
        })
    return pd.DataFrame(rows).set_index('factor')


def quantile_returns(panel, factor='composite_score', quantiles=4):
    rows = []
    spreads = []
    for date, section in panel.groupby(level='signal_date'):
        ranked = section[factor].rank(method='first')
        buckets = pd.qcut(ranked, quantiles, labels=False) + 1
        grouped = section.assign(
            quantile=buckets.to_numpy()).groupby(
                'quantile')['future_return'].mean()
        for quantile, value in grouped.items():
            rows.append({
                'signal_date': date,
                'quantile': int(quantile),
                'future_return': value,
            })
        spreads.append({
            'signal_date': date,
            'top_minus_bottom': (
                grouped.loc[quantiles] - grouped.loc[1]),
        })
    return pd.DataFrame(rows), pd.DataFrame(spreads)


def add_leave_one_out_scores(panel):
    result = panel.copy()
    for omitted in FACTOR_NAMES:
        remaining = [column for column in FACTOR_COLUMNS
                     if column != omitted + '_z']
        result['without_' + omitted] = result[remaining].mean(axis=1)
    return result


def marginal_contributions(panel):
    expanded = add_leave_one_out_scores(panel)
    columns = ('composite_score',) + tuple(
        'without_' + factor for factor in FACTOR_NAMES)
    summary = summarize_ic(information_coefficients(expanded, columns))
    full_rank_ic = summary.at['composite_score', 'mean_rank_ic']
    rows = []
    for factor in FACTOR_NAMES:
        without = summary.at['without_' + factor, 'mean_rank_ic']
        rows.append({
            'factor': factor,
            'full_rank_ic': full_rank_ic,
            'without_rank_ic': without,
            'marginal_rank_ic': full_rank_ic - without,
        })
    return pd.DataFrame(rows).set_index('factor')


def top_portfolio_turnover(panel, top):
    rows = []
    previous = None
    for date, section in panel.groupby(level='signal_date'):
        current = set(section.nlargest(top, 'composite_score').index.get_level_values(
            'symbol'))
        if previous is not None:
            rows.append({
                'signal_date': date,
                'turnover': 1.0 - len(current & previous) / float(top),
            })
        previous = current
    return pd.DataFrame(rows)


def average_factor_correlation(panel):
    matrices = []
    for _, section in panel.groupby(level='signal_date'):
        matrices.append(section[list(FACTOR_COLUMNS)].corr())
    return sum(matrices) / len(matrices)


def subset_panel(panel, start=None, end=None):
    dates = panel.index.get_level_values('signal_date')
    mask = pd.Series(True, index=panel.index)
    if start is not None:
        mask &= dates >= pd.Timestamp(start)
    if end is not None:
        mask &= dates < pd.Timestamp(end)
    return panel[mask.to_numpy()]


def print_ic_summary(title, panel):
    summary = summarize_ic(information_coefficients(panel))
    print('\n{}'.format(title))
    print('-' * 84)
    print(summary.to_string(formatters={
        'mean_ic': '{:+.3f}'.format,
        'mean_rank_ic': '{:+.3f}'.format,
        'rank_icir': '{:+.2f}'.format,
        'rank_positive': '{:.1%}'.format,
    }))
    return summary


def print_evaluation(panel, split_date, quantiles, top):
    print_ic_summary('全样本 IC / RankIC', panel)
    development = subset_panel(panel, end=split_date)
    holdout = subset_panel(panel, start=split_date)
    if not development.empty:
        print_ic_summary('开发样本（{} 之前）'.format(split_date.date()), development)
    if not holdout.empty:
        print_ic_summary('保留样本（{} 起）'.format(split_date.date()), holdout)

    quantile_frame, spread_frame = quantile_returns(
        panel, quantiles=quantiles)
    means = quantile_frame.groupby('quantile')['future_return'].mean()
    spread = spread_frame['top_minus_bottom']
    print('\n综合因子平均月度分组收益')
    print('-' * 84)
    print('  '.join('Q{}={:+.2%}'.format(index, value)
                    for index, value in means.items()))
    print('Q{}-Q1={:+.2%}  正收益月份={:.1%}'.format(
        quantiles, spread.mean(), (spread > 0).mean()))

    marginal = marginal_contributions(panel)
    holdout_marginal = marginal_contributions(holdout)
    comparison = marginal.rename(columns={
        'marginal_rank_ic': 'full_marginal',
    })[['full_marginal']].join(
        holdout_marginal.rename(columns={
            'marginal_rank_ic': 'holdout_marginal',
        })[['holdout_marginal']])
    print('\n剔除单因子的 RankIC 边际贡献（正数表示保留该因子更好）')
    print('-' * 84)
    print(comparison.to_string(formatters={
        'full_marginal': '{:+.3f}'.format,
        'holdout_marginal': '{:+.3f}'.format,
    }))

    turnover = top_portfolio_turnover(panel, top)
    print('\nTop {} 等权目标组合换手率'.format(top))
    print('-' * 84)
    print('平均={:.1%}  中位数={:.1%}  最大={:.1%}'.format(
        turnover['turnover'].mean(),
        turnover['turnover'].median(),
        turnover['turnover'].max()))

    print('\n平均截面因子相关性')
    print('-' * 84)
    print(average_factor_correlation(panel).to_string(
        float_format=lambda value: '{:+.2f}'.format(value)))


def parse_args(pargs=None):
    default_input = os.path.join(
        os.path.dirname(__file__), 'factor-scoring15-input.csv')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='月度四因子面板与 RankIC、分组收益、边际贡献、换手率')
    parser.add_argument('--input', default=default_input)
    parser.add_argument('--start', default='2021-01-31')
    parser.add_argument('--months', type=int, default=48)
    parser.add_argument('--seed', type=int, default=20260718)
    parser.add_argument('--split-date', default='',
                        help='保留样本起点；默认使用最后四分之一月份')
    parser.add_argument('--quantiles', type=int, default=4)
    parser.add_argument('--top', type=int, default=4)
    parser.add_argument('--output', default='',
                        help='可选：保存完整月度面板 CSV')
    return parser.parse_args(pargs)


def run(pargs=None):
    args = parse_args(pargs)
    base = pd.read_csv(args.input, dtype={'symbol': str})
    panel = build_teaching_panel(base, args.start, args.months, args.seed)
    audit = audit_panel(panel)

    dates = panel.index.get_level_values('signal_date')
    split_date = (
        pd.Timestamp(args.split_date) if args.split_date
        else dates.unique()[int(audit['months'] * 0.75)])

    print('=' * 84)
    print('月度四因子教学面板（模拟数据，不代表真实策略表现）')
    print('-' * 84)
    print('区间:          {} ~ {}'.format(dates.min().date(), dates.max().date()))
    print('月数 / 每月股票: {} / {}'.format(
        audit['months'], audit['assets_per_month']))
    print('面板主键:      signal_date + symbol')
    print('未来收益:      信号后下一持有期，只用于评价')
    print('样本切分:      {} 起为保留样本'.format(split_date.date()))
    print('标准化审计:    最大|均值|={:.2e}  最大|标准差-1|={:.2e}'.format(
        audit['maximum_factor_mean'], audit['maximum_factor_std_error']))
    print('=' * 84)

    print_evaluation(panel, split_date, args.quantiles, args.top)

    if args.output:
        output = os.path.abspath(args.output)
        parent = os.path.dirname(output)
        if parent:
            os.makedirs(parent, exist_ok=True)
        panel.to_csv(output)
        print('\n完整面板已写入 {}'.format(output))
    return panel


if __name__ == '__main__':
    run()

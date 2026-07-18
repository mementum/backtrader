#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# 因子研究第 13 课：IC、RankIC 与分组收益
#
# 月度对齐规则：
#   - signal_date: 当月最后一个交易日收盘后计算因子
#   - entry_date: signal_date 后第一个交易日开盘
#   - exit_date: 下一个 signal_date 后第一个交易日开盘
#   - forward_return = exit_open / entry_open - 1
#
# 因子值只使用 signal_date 当日及之前的数据；未来收益只用于评价，不参与
# 当期因子计算。脚本先做 Pandas 因子研究，不启动 Backtrader。
###############################################################################
from __future__ import absolute_import, division, print_function

import argparse
import math
import os

os.environ['NO_PROXY'] = '*'

import akshare as ak
import numpy as np
import pandas as pd


FACTOR_COLUMNS = ('momentum', 'trend', 'lowvol', 'composite')


def robust_zscore(series, clip=3.0):
    values = series.astype(float)
    median = values.median()
    scale = (values - median).abs().median() * 1.4826

    if not math.isfinite(scale) or scale < 1e-12:
        scale = values.std(ddof=0)
    if not math.isfinite(scale) or scale < 1e-12:
        return pd.Series(0.0, index=series.index)

    return ((values - median) / scale).clip(-clip, clip)


def fetch_eastmoney(symbol, fromdate, todate):
    frame = ak.stock_zh_a_hist(
        symbol=symbol,
        period='daily',
        start_date=fromdate.replace('-', ''),
        end_date=todate.replace('-', ''),
        adjust='qfq')
    return frame.rename(columns={
        '日期': 'date',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume',
    })


def fetch_sina(symbol, fromdate, todate):
    prefix = 'sh' if symbol.startswith(('5', '6', '9')) else 'sz'
    return ak.stock_zh_a_daily(
        symbol=prefix + symbol,
        start_date=fromdate.replace('-', ''),
        end_date=todate.replace('-', ''),
        adjust='qfq')


def normalize(frame, symbol):
    if frame is None or frame.empty:
        raise ValueError('未获取到 {} 的数据'.format(symbol))

    frame = frame.copy()
    frame['date'] = pd.to_datetime(frame['date'])
    frame = frame.set_index('date').sort_index()
    columns = ['open', 'high', 'low', 'close', 'volume']
    frame = frame[columns].apply(pd.to_numeric, errors='coerce')
    return frame[~frame.index.duplicated(keep='last')].dropna(
        subset=['open', 'close'])


def fetch_stock(symbol, fromdate, todate):
    try:
        frame = fetch_eastmoney(symbol, fromdate, todate)
    except Exception as exc:
        print('{} 东财源获取失败（{}），改用新浪源...'.format(
            symbol, type(exc).__name__))
        frame = fetch_sina(symbol, fromdate, todate)
    return normalize(frame, symbol)


def add_factors(frame, momentum, trend, volatility):
    result = frame.copy()
    daily_return = result['close'].pct_change()
    result['momentum'] = result['close'].pct_change(momentum)
    result['trend'] = (
        result['close'] / result['close'].rolling(trend).mean() - 1.0)
    # 转成“越高越好”的方向，因此低波动因子取负号。
    result['lowvol'] = -daily_return.rolling(volatility).std()
    return result


def build_calendar(frames):
    dates = set()
    for frame in frames.values():
        dates.update(frame.index)
    return pd.DatetimeIndex(sorted(dates))


def next_trading_date(calendar, date):
    position = calendar.searchsorted(date, side='right')
    if position >= len(calendar):
        return None
    return calendar[position]


def month_end_dates(calendar):
    dates = pd.Series(calendar, index=calendar)
    return list(dates.groupby(calendar.to_period('M')).max())


def build_factor_panel(frames, fromdate, todate, weights):
    calendar = build_calendar(frames)
    month_ends = month_end_dates(calendar)
    records = []

    for index in range(len(month_ends) - 1):
        signal_date = month_ends[index]
        next_signal_date = month_ends[index + 1]
        if signal_date < fromdate or signal_date > todate:
            continue

        entry_date = next_trading_date(calendar, signal_date)
        exit_date = next_trading_date(calendar, next_signal_date)
        if entry_date is None or exit_date is None:
            continue

        for symbol, frame in frames.items():
            required_dates = (signal_date, entry_date, exit_date)
            if not all(date in frame.index for date in required_dates):
                continue

            row = frame.loc[signal_date]
            factor_values = [
                row['momentum'], row['trend'], row['lowvol']]
            if not all(math.isfinite(float(value))
                       for value in factor_values):
                continue

            entry_open = float(frame.at[entry_date, 'open'])
            exit_open = float(frame.at[exit_date, 'open'])
            if entry_open <= 0 or exit_open <= 0:
                continue

            records.append({
                'date': signal_date,
                'symbol': symbol,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'momentum': float(row['momentum']),
                'trend': float(row['trend']),
                'lowvol': float(row['lowvol']),
                'forward_return': exit_open / entry_open - 1.0,
            })

    panel = pd.DataFrame.from_records(records)
    if panel.empty:
        raise ValueError('没有可评价的因子截面，请扩大日期范围或检查数据')

    panel = panel.set_index(['date', 'symbol']).sort_index()
    panel['composite'] = 0.0
    for factor, weight in weights.items():
        normalized = panel[factor].groupby(
            level='date', group_keys=False).transform(robust_zscore)
        panel[factor + '_z'] = normalized
        panel['composite'] += weight * normalized
    return panel


def information_coefficients(panel, minimum_assets):
    rows = []
    for date, cross_section in panel.groupby(level='date'):
        if len(cross_section) < minimum_assets:
            continue

        future = cross_section['forward_return']
        for factor in FACTOR_COLUMNS:
            values = cross_section[factor]
            if values.nunique() < 2 or future.nunique() < 2:
                continue
            rows.append({
                'date': date,
                'factor': factor,
                'ic': values.corr(future, method='pearson'),
                'rank_ic': values.corr(future, method='spearman'),
                'assets': len(cross_section),
            })

    result = pd.DataFrame.from_records(rows)
    if result.empty:
        raise ValueError('有效截面不足，无法计算 IC')
    return result


def summarize_ic(ic_frame):
    rows = []
    for factor, values in ic_frame.groupby('factor'):
        values = values.dropna(subset=['ic', 'rank_ic'])
        count = len(values)
        ic_std = values['ic'].std(ddof=1)
        rank_std = values['rank_ic'].std(ddof=1)
        rows.append({
            'factor': factor,
            'months': count,
            'mean_ic': values['ic'].mean(),
            'ic_ir': (
                values['ic'].mean() / ic_std * math.sqrt(12)
                if count > 1 and ic_std > 0 else np.nan),
            'ic_positive': (values['ic'] > 0).mean(),
            'mean_rank_ic': values['rank_ic'].mean(),
            'rank_ic_ir': (
                values['rank_ic'].mean() / rank_std * math.sqrt(12)
                if count > 1 and rank_std > 0 else np.nan),
            'rank_positive': (values['rank_ic'] > 0).mean(),
        })
    return pd.DataFrame(rows).set_index('factor').loc[
        list(FACTOR_COLUMNS)]


def quantile_returns(panel, quantiles, minimum_assets):
    quantile_rows = []
    spread_rows = []

    for date, cross_section in panel.groupby(level='date'):
        if len(cross_section) < max(minimum_assets, quantiles):
            continue

        for factor in FACTOR_COLUMNS:
            ranked = cross_section[factor].rank(method='first')
            buckets = pd.qcut(
                ranked, q=quantiles, labels=False, duplicates='drop')
            if buckets.nunique() != quantiles:
                continue

            grouped = cross_section.assign(
                quantile=buckets.to_numpy() + 1).groupby(
                    'quantile')['forward_return'].mean()
            for quantile, value in grouped.items():
                quantile_rows.append({
                    'date': date,
                    'factor': factor,
                    'quantile': int(quantile),
                    'forward_return': value,
                })

            spread_rows.append({
                'date': date,
                'factor': factor,
                'top_minus_bottom': (
                    grouped.loc[quantiles] - grouped.loc[1]),
            })

    quantile_frame = pd.DataFrame.from_records(quantile_rows)
    spread_frame = pd.DataFrame.from_records(spread_rows)
    if quantile_frame.empty or spread_frame.empty:
        raise ValueError('股票数量不足，无法完成分组收益统计')
    return quantile_frame, spread_frame


def print_ic_table(title, ic_frame):
    print('\n{}'.format(title))
    print('-' * 92)
    summary = summarize_ic(ic_frame)
    print(summary.to_string(formatters={
        'mean_ic': '{:+.3f}'.format,
        'ic_ir': '{:+.2f}'.format,
        'ic_positive': '{:.1%}'.format,
        'mean_rank_ic': '{:+.3f}'.format,
        'rank_ic_ir': '{:+.2f}'.format,
        'rank_positive': '{:.1%}'.format,
    }))


def print_quantile_table(quantile_frame, spread_frame):
    mean_returns = quantile_frame.groupby(
        ['factor', 'quantile'])['forward_return'].mean().unstack()
    spreads = spread_frame.groupby('factor')['top_minus_bottom'].agg(
        ['mean', lambda values: (values > 0).mean()])
    spreads.columns = ['monthly_spread', 'positive_rate']
    summary = mean_returns.join(spreads)
    summary = summary.loc[list(FACTOR_COLUMNS)]

    print('\n平均月度分组收益（Q1 最低分，Q5 最高分）')
    print('-' * 92)
    formatters = {
        column: '{:+.2%}'.format for column in mean_returns.columns}
    formatters.update({
        'monthly_spread': '{:+.2%}'.format,
        'positive_rate': '{:.1%}'.format,
    })
    print(summary.to_string(formatters=formatters))


def parse_weights(args):
    raw = {
        'momentum': args.momentum_weight,
        'trend': args.trend_weight,
        'lowvol': args.lowvol_weight,
    }
    total = sum(abs(value) for value in raw.values())
    if total <= 0:
        raise SystemExit('因子权重之和必须大于 0')
    return {name: value / total for name, value in raw.items()}


def run(pargs=None):
    args = parse_args(pargs)
    weights = parse_weights(args)

    evaluation_start = pd.Timestamp(args.fromdate)
    evaluation_end = pd.Timestamp(args.todate)
    maximum_lookback = max(
        args.momentum, args.trend, args.volatility)
    fetch_start = (
        evaluation_start - pd.Timedelta(days=maximum_lookback * 2)
    ).strftime('%Y-%m-%d')
    fetch_end = (
        evaluation_end + pd.Timedelta(days=75)
    ).strftime('%Y-%m-%d')

    symbols = [symbol.strip() for symbol in args.symbols.split(',')
               if symbol.strip()]
    if len(symbols) < args.minimum_assets:
        raise SystemExit('股票池数量不能小于 --minimum-assets')

    frames = {}
    for symbol in symbols:
        print('正在获取 {}...'.format(symbol))
        try:
            frame = fetch_stock(symbol, fetch_start, fetch_end)
        except Exception as exc:
            print('{} 跳过：{}'.format(symbol, exc))
            continue
        frames[symbol] = add_factors(
            frame, args.momentum, args.trend, args.volatility)

    if len(frames) < args.minimum_assets:
        raise SystemExit('成功获取的股票不足 {} 只'.format(
            args.minimum_assets))

    panel = build_factor_panel(
        frames, evaluation_start, evaluation_end, weights)
    ic_frame = information_coefficients(panel, args.minimum_assets)
    quantile_frame, spread_frame = quantile_returns(
        panel, args.quantiles, args.minimum_assets)

    dates = panel.index.get_level_values('date')
    counts = panel.groupby(level='date').size()
    print('\n' + '=' * 92)
    print('因子研究样本')
    print('-' * 92)
    print('评价区间:     {} ~ {}'.format(
        dates.min().date(), dates.max().date()))
    print('月度截面:     {} 个'.format(dates.nunique()))
    print('每期股票数:   最少 {} / 中位数 {:.0f} / 最多 {}'.format(
        counts.min(), counts.median(), counts.max()))
    print('未来收益口径: 月末信号，下一交易日开盘至下月调仓后开盘')
    print('=' * 92)

    print_ic_table('全样本 IC / RankIC', ic_frame)

    if args.split_date:
        split_date = pd.Timestamp(args.split_date)
        before = ic_frame[ic_frame['date'] < split_date]
        after = ic_frame[ic_frame['date'] >= split_date]
        if not before.empty:
            print_ic_table(
                '样本内（{} 之前）'.format(split_date.date()), before)
        if not after.empty:
            print_ic_table(
                '样本外（{} 起）'.format(split_date.date()), after)

    print_quantile_table(quantile_frame, spread_frame)

    if args.output:
        output = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(output), exist_ok=True)
        panel.to_csv(output)
        print('\n明细已写入 {}'.format(output))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='因子研究：月度 IC、RankIC 与分组收益')
    parser.add_argument(
        '--symbols',
        default=(
            '600519,000001,601318,300750,600036,000333,000651,'
            '600276,601166,600887,002415,600309,601888,002594,000858'),
        help='A 股股票池，逗号分隔')
    parser.add_argument('--fromdate', default='2020-01-01')
    parser.add_argument('--todate', default='2024-12-31')
    parser.add_argument('--split-date', default='2023-01-01',
                        help='样本内/样本外分界；传空字符串可关闭')
    parser.add_argument('--momentum', type=int, default=60)
    parser.add_argument('--trend', type=int, default=120)
    parser.add_argument('--volatility', type=int, default=20)
    parser.add_argument('--momentum-weight', type=float, default=0.5)
    parser.add_argument('--trend-weight', type=float, default=0.2)
    parser.add_argument('--lowvol-weight', type=float, default=0.3)
    parser.add_argument('--quantiles', type=int, default=5)
    parser.add_argument('--minimum-assets', type=int, default=10)
    parser.add_argument('--output', default='',
                        help='可选：保存因子面板 CSV 的路径')
    return parser.parse_args(pargs)


if __name__ == '__main__':
    run()

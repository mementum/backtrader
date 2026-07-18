#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# 因子研究第 17 课：真实数据月度四因子面板
#
# 数据：
#   - AKShare / 东方财富真实前复权日线
#   - 东方财富历史总市值
#   - 东方财富季度财务快照：公告日、更新日、ROE、归母净利润
#
# 修订处理：
#   当前接口没有保留修订前的旧指标值。若 UPDATE_DATE 晚于 NOTICE_DATE，
#   当前快照值只从 UPDATE_DATE 后的下一交易日开始使用。这个口径保守地
#   避免把当前修订值提前使用，但不能还原修订前市场真正看到的旧值。
###############################################################################
from __future__ import absolute_import, division, print_function

import argparse
import importlib.util
import os
import time

os.environ['NO_PROXY'] = '*'

import akshare as ak
import numpy as np
import pandas as pd
import requests


def load_sibling(filename, module_name):
    path = os.path.join(os.path.dirname(__file__), filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCORING = load_sibling('factor-scoring15.py', 'factor_scoring15')
EVALUATION = load_sibling('factor-panel16.py', 'factor_panel16')
PRICE_RESEARCH = load_sibling('factor-research13.py', 'factor_research13')

FUNDAMENTAL_URL = 'https://datacenter-web.eastmoney.com/api/data/v1/get'


def cache_path(cache_dir, category, symbol, suffix=''):
    filename = '{}-{}{}.csv'.format(category, symbol, suffix)
    return os.path.join(os.path.expanduser(cache_dir), filename)


def read_cached(path, date_columns):
    frame = pd.read_csv(path, dtype={'symbol': str})
    for column in date_columns:
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors='coerce')
    return frame


def write_cached(frame, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frame.to_csv(path, index=False)


def fetch_prices(symbol, fromdate, todate, cache_dir, refresh):
    suffix = '-{}-{}'.format(fromdate.replace('-', ''), todate.replace('-', ''))
    path = cache_path(cache_dir, 'prices', symbol, suffix)
    if os.path.exists(path) and not refresh:
        frame = read_cached(path, ('date',))
    else:
        frame = PRICE_RESEARCH.fetch_stock(symbol, fromdate, todate)
        frame = frame.reset_index()
        frame['symbol'] = symbol
        write_cached(frame, path)

    frame = frame.set_index('date').sort_index()
    return frame[~frame.index.duplicated(keep='last')]


def retry_fetch(fetcher, label, retries=3):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return fetcher()
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt)
    raise RuntimeError('{} 获取失败: {}'.format(label, last_error))


def fetch_valuation(symbol, cache_dir, refresh):
    path = cache_path(cache_dir, 'valuation', symbol)
    if os.path.exists(path) and not refresh:
        return read_cached(path, ('date',))

    frame = retry_fetch(
        lambda: ak.stock_value_em(symbol=symbol),
        '{} 历史估值'.format(symbol))
    frame = frame.rename(columns={
        '数据日期': 'date',
        '当日收盘价': 'valuation_close',
        '总市值': 'market_cap',
        '总股本': 'total_shares',
        'PE(TTM)': 'provider_pe_ttm',
    })
    frame['date'] = pd.to_datetime(frame['date'], errors='coerce')
    frame['symbol'] = symbol
    columns = [
        'date', 'symbol', 'valuation_close', 'market_cap',
        'total_shares', 'provider_pe_ttm',
    ]
    frame = frame[columns].dropna(subset=['date', 'market_cap'])
    write_cached(frame, path)
    return frame


def fetch_fundamental(symbol, cache_dir, refresh):
    path = cache_path(cache_dir, 'fundamental', symbol)
    date_columns = ('report_date', 'notice_date', 'update_date')
    if os.path.exists(path) and not refresh:
        return read_cached(path, date_columns)

    params = {
        'sortColumns': 'REPORTDATE',
        'sortTypes': '1',
        'pageSize': '500',
        'pageNumber': '1',
        'reportName': 'RPT_LICO_FN_CPD',
        'columns': 'ALL',
        'filter': '(SECURITY_CODE="{}")'.format(symbol),
    }

    def request_rows():
        response = requests.get(FUNDAMENTAL_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return (payload.get('result') or {}).get('data') or []

    rows = retry_fetch(request_rows, '{} 季度财务'.format(symbol))
    if not rows:
        raise ValueError('{} 没有季度财务记录'.format(symbol))

    raw = pd.DataFrame(rows)
    frame = pd.DataFrame({
        'symbol': raw['SECURITY_CODE'].astype(str).str.zfill(6),
        'name': raw['SECURITY_NAME_ABBR'],
        'report_date': pd.to_datetime(raw['REPORTDATE'], errors='coerce'),
        'notice_date': pd.to_datetime(raw['NOTICE_DATE'], errors='coerce'),
        'update_date': pd.to_datetime(raw['UPDATE_DATE'], errors='coerce'),
        'reported_roe': pd.to_numeric(
            raw['WEIGHTAVG_ROE'], errors='coerce') / 100.0,
        'parent_net_profit': pd.to_numeric(
            raw['PARENT_NETPROFIT'], errors='coerce'),
    })
    frame = frame.dropna(subset=[
        'report_date', 'notice_date', 'update_date',
        'reported_roe', 'parent_net_profit',
    ])
    frame = frame.sort_values(['report_date', 'update_date']).drop_duplicates(
        subset=['report_date'], keep='last')
    write_cached(frame, path)
    return frame.reset_index(drop=True)


def build_calendar(price_frames):
    dates = set()
    for frame in price_frames.values():
        dates.update(frame.index)
    return pd.DatetimeIndex(sorted(dates))


def next_trading_date(calendar, date):
    position = calendar.searchsorted(pd.Timestamp(date), side='right')
    if position >= len(calendar):
        return pd.NaT
    return calendar[position]


def month_end_dates(calendar):
    values = pd.Series(calendar, index=calendar)
    return pd.DatetimeIndex(
        values.groupby(calendar.to_period('M')).max().to_numpy())


def prepare_fundamentals(frame, calendar, availability_mode):
    result = frame.copy()
    result['revision_lag_days'] = (
        result['update_date'] - result['notice_date']).dt.days
    result['revision_risk'] = result['revision_lag_days'] > 0
    if availability_mode == 'snapshot-safe':
        result['snapshot_available_date'] = result[[
            'notice_date', 'update_date']].max(axis=1)
    else:
        result['snapshot_available_date'] = result['notice_date']
    result['effective_date'] = result['snapshot_available_date'].map(
        lambda date: next_trading_date(calendar, date))

    report_month = result['report_date'].dt.month
    annualization = 12.0 / report_month
    result['annualized_roe'] = result['reported_roe'] * annualization
    result['annualized_net_profit'] = (
        result['parent_net_profit'] * annualization)
    return result.dropna(subset=['effective_date']).sort_values(
        ['effective_date', 'report_date'])


def last_row_on_or_before(frame, date, date_column):
    dates = frame[date_column].to_numpy(dtype='datetime64[ns]')
    position = dates.searchsorted(np.datetime64(date), side='right') - 1
    if position < 0:
        return None
    return frame.iloc[position]


def price_factors(frame, signal_date, momentum_long, momentum_skip, volatility):
    try:
        position = frame.index.get_loc(signal_date)
    except KeyError:
        return None
    if not isinstance(position, (int, np.integer)):
        return None
    if position < max(momentum_long, volatility):
        return None

    close = frame['close']
    recent_price = float(close.iloc[position - momentum_skip])
    old_price = float(close.iloc[position - momentum_long])
    returns = close.pct_change().iloc[
        position - volatility + 1:position + 1]
    if old_price <= 0 or recent_price <= 0 or len(returns.dropna()) < volatility:
        return None
    return {
        'momentum_12_1': recent_price / old_price - 1.0,
        'volatility_120': returns.std(ddof=0) * np.sqrt(252.0),
    }


def build_real_panel(
        universe, price_frames, valuation_frames, fundamental_frames,
        fromdate, todate, momentum_long, momentum_skip, volatility,
        minimum_assets, availability_mode):
    calendar = build_calendar(price_frames)
    month_ends = month_end_dates(calendar)
    prepared_fundamentals = {
        symbol: prepare_fundamentals(frame, calendar, availability_mode)
        for symbol, frame in fundamental_frames.items()
    }
    prepared_valuations = {
        symbol: frame.sort_values('date').reset_index(drop=True)
        for symbol, frame in valuation_frames.items()
    }
    universe_by_symbol = universe.set_index('symbol')
    records = []
    skip_counts = {}

    def skip(reason):
        skip_counts[reason] = skip_counts.get(reason, 0) + 1

    for index in range(len(month_ends) - 1):
        signal_date = month_ends[index]
        next_signal_date = month_ends[index + 1]
        if signal_date < fromdate or signal_date > todate:
            continue

        entry_date = next_trading_date(calendar, signal_date)
        exit_date = next_trading_date(calendar, next_signal_date)
        if pd.isna(entry_date) or pd.isna(exit_date):
            continue

        cross_section = []
        for symbol in universe['symbol']:
            prices = price_frames.get(symbol)
            valuation = prepared_valuations.get(symbol)
            fundamentals = prepared_fundamentals.get(symbol)
            if prices is None or valuation is None or fundamentals is None:
                skip('missing_source')
                continue
            if not all(date in prices.index
                       for date in (signal_date, entry_date, exit_date)):
                skip('not_tradable_on_required_date')
                continue

            technical = price_factors(
                prices, signal_date,
                momentum_long, momentum_skip, volatility)
            if technical is None:
                skip('insufficient_price_history')
                continue

            valuation_row = last_row_on_or_before(
                valuation, signal_date, 'date')
            fundamental_row = last_row_on_or_before(
                fundamentals, signal_date, 'effective_date')
            if valuation_row is None or fundamental_row is None:
                skip('fundamental_or_valuation_unavailable')
                continue

            market_cap = float(valuation_row['market_cap'])
            annualized_profit = float(
                fundamental_row['annualized_net_profit'])
            if not np.isfinite(market_cap) or market_cap <= 0:
                skip('invalid_market_cap')
                continue

            entry_open = float(prices.at[entry_date, 'open'])
            exit_open = float(prices.at[exit_date, 'open'])
            if entry_open <= 0 or exit_open <= 0:
                skip('invalid_execution_price')
                continue

            info = universe_by_symbol.loc[symbol]
            cross_section.append({
                'symbol': symbol,
                'name': info['name'],
                'industry': info['industry'],
                'market_cap': market_cap,
                'earnings_yield': annualized_profit / market_cap,
                'roe': float(fundamental_row['annualized_roe']),
                'momentum_12_1': technical['momentum_12_1'],
                'volatility_120': technical['volatility_120'],
                'report_date': fundamental_row['report_date'],
                'valuation_date': valuation_row['date'],
                'reported_roe': fundamental_row['reported_roe'],
                'annualized_net_profit': annualized_profit,
                'notice_date': fundamental_row['notice_date'],
                'update_date': fundamental_row['update_date'],
                'effective_date': fundamental_row['effective_date'],
                'revision_lag_days': int(
                    fundamental_row['revision_lag_days']),
                'revision_risk': bool(fundamental_row['revision_risk']),
                'entry_date': entry_date,
                'exit_date': exit_date,
                'future_return': exit_open / entry_open - 1.0,
            })

        if len(cross_section) < minimum_assets:
            skip('cross_section_below_minimum')
            continue

        raw = pd.DataFrame(cross_section)
        scored = SCORING.score_factors(raw)
        scored['signal_date'] = signal_date
        records.append(scored)

    if not records:
        raise ValueError('没有形成有效月度截面，请检查网络、缓存和日期范围')
    panel = pd.concat(records, ignore_index=True)
    panel = panel.set_index(['signal_date', 'symbol']).sort_index()
    return panel, skip_counts


def fetch_sources(universe, fetch_start, fetch_end, cache_dir, refresh):
    price_frames = {}
    valuation_frames = {}
    fundamental_frames = {}
    failures = {}

    for symbol in universe['symbol']:
        print('获取 {} 真实数据...'.format(symbol))
        try:
            price_frames[symbol] = fetch_prices(
                symbol, fetch_start, fetch_end, cache_dir, refresh)
            valuation_frames[symbol] = fetch_valuation(
                symbol, cache_dir, refresh)
            fundamental_frames[symbol] = fetch_fundamental(
                symbol, cache_dir, refresh)
        except Exception as exc:
            failures[symbol] = str(exc)
            print('  跳过 {}: {}'.format(symbol, exc))
    return price_frames, valuation_frames, fundamental_frames, failures


def print_real_audit(panel, failures, skip_counts, availability_mode):
    dates = panel.index.get_level_values('signal_date')
    counts = panel.groupby(level='signal_date').size()
    revision = panel['revision_risk']
    report_ages = (
        dates - pd.DatetimeIndex(panel['report_date'])).days

    print('\n' + '=' * 92)
    print('真实数据月度四因子面板')
    print('-' * 92)
    print('区间:              {} ~ {}'.format(
        dates.min().date(), dates.max().date()))
    print('有效月份:          {}'.format(dates.nunique()))
    print('每月股票数:        最少 {} / 中位数 {:.0f} / 最多 {}'.format(
        counts.min(), counts.median(), counts.max()))
    print('财务生效口径:      {}'.format(availability_mode))
    print('财报修订风险观察:  {} / {} ({:.1%})'.format(
        revision.sum(), len(revision), revision.mean()))
    print('所用财报年龄:      中位数 {:.0f} 天 / 最大 {} 天'.format(
        np.median(report_ages), report_ages.max()))
    print('数据源失败股票:    {}'.format(len(failures)))
    print('跳过记录:          {}'.format(
        ', '.join('{}={}'.format(key, value)
                  for key, value in sorted(skip_counts.items())) or '无'))
    print('=' * 92)
    print('警告: 固定股票名单存在幸存者偏差；历史估值和财务值来自供应商当前接口。')
    if availability_mode == 'snapshot-safe':
        print('      UPDATE_DATE 晚于公告日时已延后生效，但仍无法还原修订前旧值。')
    else:
        print('      notice-date 会把当前修订值放到首次公告日，结果存在修订前视风险。')


def load_universe(path, symbols):
    universe = pd.read_csv(path, dtype={'symbol': str})[[
        'symbol', 'name', 'industry']]
    universe['symbol'] = universe['symbol'].str.zfill(6)
    if symbols:
        selected = [value.strip().zfill(6)
                    for value in symbols.split(',') if value.strip()]
        universe = universe[universe['symbol'].isin(selected)]
    if len(universe) < 10:
        raise ValueError('行业中性化的真实数据示例至少需要 10 只股票')
    if len(universe) <= universe['industry'].nunique() + 1:
        raise ValueError('每个行业需要足够股票，才能同时完成行业和市值中性化')
    return universe.reset_index(drop=True)


def parse_args(pargs=None):
    default_universe = os.path.join(
        os.path.dirname(__file__), 'factor-scoring15-input.csv')
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='真实 A 股月度四因子：公告/更新日对齐、RankIC 与分组收益')
    parser.add_argument('--universe', default=default_universe)
    parser.add_argument('--symbols', default='', help='可选股票代码，逗号分隔')
    parser.add_argument('--fromdate', default='2021-01-01')
    parser.add_argument('--todate', default='2025-12-31')
    parser.add_argument('--split-date', default='2024-01-01')
    parser.add_argument('--momentum-long', type=int, default=252)
    parser.add_argument('--momentum-skip', type=int, default=21)
    parser.add_argument('--volatility', type=int, default=120)
    parser.add_argument('--minimum-assets', type=int, default=10)
    parser.add_argument(
        '--availability-mode',
        choices=('snapshot-safe', 'notice-date'),
        default='snapshot-safe',
        help='财务快照生效口径；notice-date 仅用于泄漏敏感性对照')
    parser.add_argument('--quantiles', type=int, default=4)
    parser.add_argument('--top', type=int, default=4)
    parser.add_argument(
        '--cache-dir', default='~/.cache/backtrader-factor-real17')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--output', default='', help='可选：保存完整真实面板 CSV')
    return parser.parse_args(pargs)


def run(pargs=None):
    args = parse_args(pargs)
    fromdate = pd.Timestamp(args.fromdate)
    todate = pd.Timestamp(args.todate)
    split_date = pd.Timestamp(args.split_date)
    universe = load_universe(args.universe, args.symbols)

    fetch_start = (
        fromdate - pd.Timedelta(days=args.momentum_long * 2.2)
    ).strftime('%Y-%m-%d')
    fetch_end = (
        todate + pd.Timedelta(days=70)
    ).strftime('%Y-%m-%d')
    sources = fetch_sources(
        universe, fetch_start, fetch_end,
        args.cache_dir, args.refresh)
    price_frames, valuation_frames, fundamental_frames, failures = sources

    panel, skip_counts = build_real_panel(
        universe, price_frames, valuation_frames, fundamental_frames,
        fromdate, todate,
        args.momentum_long, args.momentum_skip, args.volatility,
        args.minimum_assets, args.availability_mode)
    print_real_audit(
        panel, failures, skip_counts, args.availability_mode)
    EVALUATION.print_evaluation(
        panel, split_date, args.quantiles, args.top)

    if args.output:
        output = os.path.abspath(args.output)
        parent = os.path.dirname(output)
        if parent:
            os.makedirs(parent, exist_ok=True)
        panel.to_csv(output)
        print('\n完整真实面板已写入 {}'.format(output))
    return panel


if __name__ == '__main__':
    run()

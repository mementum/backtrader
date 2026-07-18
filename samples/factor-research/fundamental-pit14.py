#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# 基本面研究第 14 课：公告日对齐与修订风险
#
# 数据源：
#   - 东方财富业绩报表：当前快照中的 ROE、净利润同比增长、最新更新日期
#   - 巨潮资讯公告：原始定期报告的首次披露日期
#
# 重要限制：
#   东方财富接口返回当前快照，不保证保留每次历史修订时的旧指标值。因此本
#   脚本可以演示“按首次公告日生效”，但不能把当前指标值还原成完整的历史
#   point-in-time 数据。发现快照更新日晚于首次披露日时，会明确标记修订风险。
###############################################################################
from __future__ import absolute_import, division, print_function

import argparse
import math
import os
import re
import time

os.environ['NO_PROXY'] = '*'

import akshare as ak
import numpy as np
import pandas as pd
import requests


REPORT_CONFIGS = (
    {
        'report_date': '2023-09-30',
        'category': '三季报',
        'title_token': '2023年第三季度报告',
        'search_start': '20231001',
        'search_end': '20231130',
    },
    {
        'report_date': '2023-12-31',
        'category': '年报',
        'title_token': '2023年年度报告',
        'search_start': '20240101',
        'search_end': '20240531',
    },
    {
        'report_date': '2024-03-31',
        'category': '一季报',
        'title_token': '2024年第一季度报告',
        'search_start': '20240301',
        'search_end': '20240531',
    },
    {
        'report_date': '2024-06-30',
        'category': '半年报',
        'title_token': '2024年半年度报告',
        'search_start': '20240701',
        'search_end': '20240930',
    },
    {
        'report_date': '2024-09-30',
        'category': '三季报',
        'title_token': '2024年第三季度报告',
        'search_start': '20241001',
        'search_end': '20241130',
    },
)

EXCLUDED_TITLE_WORDS = (
    '摘要', '英文', '修订', '更正', '补充', '取消', '审计报告')


def compact_title(value):
    return re.sub(r'\s+', '', str(value))


def robust_zscore(series):
    values = pd.to_numeric(series, errors='coerce')
    median = values.median()
    scale = (values - median).abs().median() * 1.4826
    if not math.isfinite(scale) or scale < 1e-12:
        scale = values.std(ddof=0)
    if not math.isfinite(scale) or scale < 1e-12:
        return pd.Series(0.0, index=series.index)
    return ((values - median) / scale).clip(-3.0, 3.0)


def fetch_metric_row(config, symbol, retries=3):
    url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
    params = {
        'sortColumns': 'UPDATE_DATE,SECURITY_CODE',
        'sortTypes': '-1,-1',
        'pageSize': '20',
        'pageNumber': '1',
        'reportName': 'RPT_LICO_FN_CPD',
        'columns': 'ALL',
        'filter': (
            "(REPORTDATE='{}')(SECURITY_CODE=\"{}\")".format(
                config['report_date'], symbol)),
    }

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            payload = response.json()
            data = (payload.get('result') or {}).get('data') or []
            if not data:
                raise ValueError('接口未返回记录')
            row = data[0]
            return {
                'symbol': row['SECURITY_CODE'],
                'name': row['SECURITY_NAME_ABBR'],
                'report_date': pd.to_datetime(
                    row['REPORTDATE'], errors='coerce'),
                'roe': pd.to_numeric(
                    row['WEIGHTAVG_ROE'], errors='coerce'),
                'profit_growth': pd.to_numeric(
                    row['SJLTZ'], errors='coerce'),
                'source_notice_date': pd.to_datetime(
                    row['NOTICE_DATE'], errors='coerce'),
                'snapshot_update_date': pd.to_datetime(
                    row['UPDATE_DATE'], errors='coerce'),
            }
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt)
    raise RuntimeError('{} {} 获取失败: {}'.format(
        symbol, config['report_date'], last_error))


def fetch_metric_snapshot(config, symbols):
    print('获取 {} 业绩指标快照...'.format(config['report_date']))
    rows = []
    for symbol in symbols:
        rows.append(fetch_metric_row(config, symbol))
    return pd.DataFrame(rows)


def fetch_first_disclosure(symbol, config):
    frame = ak.stock_zh_a_disclosure_report_cninfo(
        symbol=symbol,
        market='沪深京',
        category=config['category'],
        start_date=config['search_start'],
        end_date=config['search_end'])
    if frame.empty:
        return pd.NaT, ''

    title_token = compact_title(config['title_token'])
    titles = frame['公告标题'].map(compact_title)
    matches = titles.str.contains(title_token, regex=False)
    for word in EXCLUDED_TITLE_WORDS:
        matches &= ~titles.str.contains(word, regex=False)

    candidates = frame[matches].copy()
    if candidates.empty:
        return pd.NaT, ''

    candidates['公告时间'] = pd.to_datetime(
        candidates['公告时间'], errors='coerce')
    candidates = candidates.dropna(subset=['公告时间']).sort_values('公告时间')
    if candidates.empty:
        return pd.NaT, ''

    first = candidates.iloc[0]
    return first['公告时间'].normalize(), first['公告标题']


def build_report_history(symbols):
    metric_frames = [
        fetch_metric_snapshot(config, symbols)
        for config in REPORT_CONFIGS
    ]
    history = pd.concat(metric_frames, ignore_index=True)

    disclosures = []
    for symbol in symbols:
        for config in REPORT_CONFIGS:
            print('查询 {} {} 首次披露...'.format(
                symbol, config['title_token']))
            try:
                first_date, title = fetch_first_disclosure(symbol, config)
            except Exception as exc:
                print('  查询失败: {}'.format(exc))
                first_date, title = pd.NaT, ''
            disclosures.append({
                'symbol': symbol,
                'report_date': pd.Timestamp(config['report_date']),
                'first_disclosure_date': first_date,
                'disclosure_title': title,
            })

    disclosure_frame = pd.DataFrame(disclosures)
    history = history.merge(
        disclosure_frame,
        on=['symbol', 'report_date'],
        how='left')

    history = history.rename(columns={
        'first_disclosure_date': 'cninfo_disclosure_date',
    })
    history['first_disclosure_date'] = history[
        'cninfo_disclosure_date'].combine_first(
            history['source_notice_date'])
    history['notice_matches_cninfo'] = (
        history['source_notice_date'].dt.normalize()
        == history['cninfo_disclosure_date'].dt.normalize())

    # 只有日期而没有具体发布时间时，保守地从下一日开始允许使用。
    history['effective_date'] = (
        history['first_disclosure_date'] + pd.Timedelta(days=1))
    history['first_disclosure_lag'] = (
        history['first_disclosure_date'] - history['report_date']).dt.days
    history['snapshot_revision_lag'] = (
        history['snapshot_update_date']
        - history['first_disclosure_date']).dt.days
    history['revision_risk'] = history['snapshot_revision_lag'] > 0
    return history.sort_values(['symbol', 'report_date'])


def asof_by_symbol(signals, history, mode):
    rows = []
    date_column = 'report_date' if mode == 'naive' else 'effective_date'

    for symbol in signals['symbol'].unique():
        left = signals[signals['symbol'] == symbol].sort_values(
            'signal_date').copy()
        right = history[history['symbol'] == symbol].dropna(
            subset=[date_column]).sort_values(date_column).copy()
        right = right.drop(columns=['symbol'])

        merged = pd.merge_asof(
            left,
            right,
            left_on='signal_date',
            right_on=date_column,
            direction='backward')
        merged['mode'] = mode
        rows.append(merged)

    return pd.concat(rows, ignore_index=True)


def build_monthly_panel(history, symbols, start_date, end_date):
    signal_dates = pd.date_range(
        start=start_date, end=end_date, freq='ME')
    signals = pd.MultiIndex.from_product(
        [signal_dates, symbols],
        names=['signal_date', 'symbol']).to_frame(index=False)

    naive = asof_by_symbol(signals, history, mode='naive')
    safe = asof_by_symbol(signals, history, mode='announcement_aware')
    panel = naive.merge(
        safe,
        on=['signal_date', 'symbol'],
        how='outer',
        suffixes=('_naive', '_safe'))

    panel['is_leaked'] = (
        panel['report_date_naive'].notna()
        & (
            panel['report_date_safe'].isna()
            | (panel['report_date_naive'] > panel['report_date_safe'])
        )
    )
    return panel


def score_cross_sections(panel, mode):
    suffix = 'naive' if mode == 'naive' else 'safe'
    report_column = 'report_date_' + suffix
    roe_column = 'roe_' + suffix
    growth_column = 'profit_growth_' + suffix

    records = []
    for signal_date, section in panel.groupby('signal_date'):
        available = section.dropna(
            subset=[report_column, roe_column, growth_column]).copy()
        if len(available) < 2:
            continue

        available['quality_score'] = (
            0.6 * robust_zscore(available[roe_column])
            + 0.4 * robust_zscore(available[growth_column]))
        available = available.sort_values(
            'quality_score', ascending=False)
        for rank, (_, row) in enumerate(available.iterrows(), 1):
            records.append({
                'signal_date': signal_date,
                'mode': mode,
                'rank': rank,
                'symbol': row['symbol'],
                'report_date': row[report_column],
                'roe': row[roe_column],
                'profit_growth': row[growth_column],
                'quality_score': row['quality_score'],
            })
    return pd.DataFrame(records)


def print_history_audit(history):
    print('\n' + '=' * 106)
    print('财务数据时点审计')
    print('-' * 106)
    print(history[[
        'symbol', 'report_date', 'source_notice_date',
        'cninfo_disclosure_date', 'first_disclosure_date',
        'snapshot_update_date', 'first_disclosure_lag',
        'snapshot_revision_lag', 'revision_risk',
    ]].to_string(index=False, formatters={
        'report_date': lambda value: value.strftime('%Y-%m-%d'),
        'source_notice_date': (
            lambda value: value.strftime('%Y-%m-%d')
            if pd.notna(value) else 'N/A'),
        'cninfo_disclosure_date': (
            lambda value: value.strftime('%Y-%m-%d')
            if pd.notna(value) else 'N/A'),
        'first_disclosure_date': (
            lambda value: value.strftime('%Y-%m-%d')
            if pd.notna(value) else 'N/A'),
        'snapshot_update_date': (
            lambda value: value.strftime('%Y-%m-%d')
            if pd.notna(value) else 'N/A'),
    }))
    print('=' * 106)


def print_alignment_comparison(panel):
    total = len(panel)
    leaked = int(panel['is_leaked'].sum())
    print('\n月末可用报告对齐')
    print('-' * 106)
    print('股票-月份观察数: {}'.format(total))
    print('报告期法提前使用: {}（{:.1%}）'.format(
        leaked, leaked / total if total else 0.0))

    examples = panel[panel['is_leaked']][[
        'signal_date', 'symbol', 'report_date_naive',
        'report_date_safe', 'first_disclosure_date_naive']]
    if not examples.empty:
        print('\n前视样例（最多 12 条）:')
        print(examples.head(12).to_string(index=False))


def print_ranking_comparison(rankings, topk):
    print('\n质量因子 Top {}：报告期法 vs 公告日法'.format(topk))
    print('-' * 106)
    top = rankings[rankings['rank'] <= topk]
    ordered = top.groupby(['signal_date', 'mode'])['symbol'].apply(
        lambda values: tuple(values)).unstack()
    pivot = ordered.map(
        lambda values: ','.join(values)
        if isinstance(values, tuple) else '')
    pivot['order_different'] = (
        ordered.get('naive') != ordered.get('announcement_aware'))
    pivot['set_different'] = [
        set(naive or ()) != set(safe or ())
        for naive, safe in zip(
            ordered.get('naive', pd.Series(index=ordered.index)),
            ordered.get(
                'announcement_aware',
                pd.Series(index=ordered.index)))
    ]
    print(pivot.to_string())
    if len(pivot):
        print('\nTop {} 持仓集合不同: {} / {}（{:.1%}）'.format(
            topk,
            int(pivot['set_different'].sum()),
            len(pivot),
            pivot['set_different'].mean()))
        print('Top {} 排名顺序不同: {} / {}（{:.1%}）'.format(
            topk,
            int(pivot['order_different'].sum()),
            len(pivot),
            pivot['order_different'].mean()))


def run(pargs=None):
    args = parse_args(pargs)
    symbols = [symbol.strip() for symbol in args.symbols.split(',')
               if symbol.strip()]
    if len(symbols) < 2:
        raise SystemExit('至少需要 2 只股票')

    history = build_report_history(symbols)
    panel = build_monthly_panel(
        history, symbols, args.fromdate, args.todate)
    rankings = pd.concat([
        score_cross_sections(panel, 'naive'),
        score_cross_sections(panel, 'announcement_aware'),
    ], ignore_index=True)

    print_history_audit(history)
    print_alignment_comparison(panel)
    print_ranking_comparison(rankings, args.topk)

    revision_count = int(history['revision_risk'].sum())
    print('\n研究结论')
    print('-' * 106)
    print('1. 报告期不能作为可用日期；本样本有 {} 条股票-月份记录会提前使用财报。'.format(
        int(panel['is_leaked'].sum())))
    print('2. {} / {} 条报告的当前快照更新日晚于首次披露日，存在历史修订风险。'.format(
        revision_count, len(history)))
    print('3. 本脚本适合教学和数据审计，不足以支持正式的历史基本面因子回测。')

    if args.output:
        output = os.path.abspath(args.output)
        os.makedirs(output, exist_ok=True)
        history.to_csv(
            os.path.join(output, 'fundamental-history14.csv'),
            index=False)
        panel.to_csv(
            os.path.join(output, 'fundamental-alignment14.csv'),
            index=False)
        rankings.to_csv(
            os.path.join(output, 'fundamental-rankings14.csv'),
            index=False)
        print('\n明细已写入 {}'.format(output))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='基本面因子：报告期、首次披露日与快照修订风险')
    parser.add_argument(
        '--symbols',
        default='600519,000001,601318,300750,600036',
        help='股票代码，逗号分隔')
    parser.add_argument('--fromdate', default='2023-12-31')
    parser.add_argument('--todate', default='2024-11-30')
    parser.add_argument('--topk', type=int, default=2)
    parser.add_argument('--output', default='',
                        help='可选：输出三个 CSV 的目录')
    return parser.parse_args(pargs)


if __name__ == '__main__':
    run()

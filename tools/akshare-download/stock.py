import os
from typing import List
import akshare as ak
import pandas as pd
import datetime
import multiprocessing
from progress.bar import IncrementalBar
from tqdm import tqdm

mainpath = os.path.dirname(os.path.dirname(__file__)) + '../../datas/stock'

'''
获取股票数据
'''

def get_a_stock_list():
    """
    获取A股股票清单
    沪深京三个交易所
    """
    df = eval('ak.stock_zh_a_spot_em')()
    path = os.path.join(mainpath, f'a_stock_list.csv')
    df.to_csv(path, encoding='utf-8')

def get_a_zb_stock_list():
    """
    获取A股股票清单-主板：60， 00开头
    """
    df = ak.stock_zh_a_spot_em()
    df = df[df.代码.str.startswith(('60', '00',))]
    path = os.path.join(mainpath, f'a_zb_stock_list.csv')
    df.to_csv(path, encoding='utf-8')

def get_us_stock_list():
    """
    获取美股股票清单
    """
    df = ak.stock_us_spot_em()

    path = os.path.join(mainpath, 'us_stock_list.csv')
    df.to_csv(path, encoding='utf-8')

def upsert_stock_detail(type: str, symbol: str, start_date: str, end_date: str = datetime.datetime.now().strftime('%Y%m%d'), period: str = 'daily'):
    """
    获取每日后复权股票数据
    type: us | zh_a
    symbol: 股票代码
    start_date: 开始日期
    end_date: 结束日期
    period: daily | weekly | monthly
    当日收盘后更新
    """
    dir = os.path.join(mainpath, f'{type}')
    if not os.path.exists(dir):
        os.makedirs(dir)
    path = os.path.join(dir, f'{symbol}.csv')
    # 如果已经存在，更新数据
    if os.path.exists(path):
        old_df = pd.read_csv(path)
        if old_df.shape[0] > 0: # 如果有数据
            start_date = str(int(old_df['日期'].iloc[-1].replace('-', '')) + 1)
        else: # 没有数据就删除
            os.remove(path)
        stock_data = eval('ak.stock_' + type + '_hist')(symbol=symbol, period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
        if stock_data.shape[0] < 1: # 成功返回却没有数据
            print(f'{symbol}没有新数据可更新')
        else:
            new_df = pd.concat([old_df, stock_data])
            new_df.to_csv(path, encoding='utf-8')
    else:
        stock_data = eval('ak.stock_' + type + '_hist')(symbol=symbol, period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
        if stock_data.shape[0] < 1: # 成功返回却没有数据
            print(f'{symbol}下载成功，但没有返回数据，有可能已经退市')
        else:
            stock_data.to_csv(path, encoding='utf-8')
    

def name_list(csv_name):
    import csv
    csv_f = os.path.join(mainpath, f'{csv_name}')
    stock_list = []
    with open(csv_f, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['名称'].startswith('N'):
                stock_list.append(row['代码'])
            else:
                print(row['名称'])
    return stock_list


def get_stock_list_task(stock_list: List[str]):
    bar = IncrementalBar('Download', max=len(stock_list))
    type = 'zh_a'
    start_date='20220101'
    end_date=datetime.datetime.now().strftime('%Y%m%d')
    period = 'daily'
    failed_num = 0
    for symbol in stock_list:
        try:
            upsert_stock_detail(type, symbol, start_date, end_date, period)
            bar.next()
        except Exception as e:
            print(f'不能下载: {symbol}, error: {e}')
            failed_num += 1
            bar.next()
    bar.finish()
    return len(stock_list) - failed_num

if __name__ == '__main__':
    # get_a_zb_stock_list()

    # 多进程下载或更新所有A股股票
    cpu_count = max(int(multiprocessing.cpu_count() - 2), 1)
    pool = multiprocessing.Pool(cpu_count)
    
    stock_list = name_list('a_stock_list.csv')
    stock_list = stock_list[0:15]
    pbar = tqdm(total=len(stock_list))
    # 每20支股票一组
    n = 3
    stock_lists = [stock_list[i:i + n] for i in range(0, len(stock_list), n)]
    # tqdm(pool.imap(get_stock_list_task, stock_lists), total=len(stock_lists))
    def bar_update(num):
        pbar.update(num)
        print(f'{pbar.n} / {pbar.total} / {pbar.leave}')

    for stock_list in stock_lists:
        # get_stock_detail_task(bar, type, symbol, start_date, end_date, period)
        pool.apply_async(func=get_stock_list_task, args=(stock_list,), callback=bar_update)

    pool.close()
    pool.join()
    pbar.close()
    print(f'下载完成, 成功：{pbar.n}, 失败：{pbar.total - pbar.n}')
    # start_date='20220101'
    # end_date=datetime.datetime.now().strftime('%Y%m%d')
    # upsert_stock_detail('zh_a', '000618', start_date, end_date)
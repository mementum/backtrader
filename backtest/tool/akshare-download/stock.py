import os
from typing import List
import akshare as ak
import pandas as pd
import datetime
import multiprocessing
from progress.bar import IncrementalBar
from tqdm import tqdm

mainpath = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
mainpath = os.path.join(mainpath, 'datas/stock')

'''
Download stock datas
'''

def get_stock_list(type: str):
    """
    Get all A or US stock name list
    type: zh_a | us
    """
    if not os.path.exists(mainpath):
        os.makedirs(mainpath)
    df = eval(f'ak.stock_{type}_spot_em')()
    path = os.path.join(mainpath, f'{type}_stock_list.csv')
    df.to_csv(path, encoding='utf-8')

def get_a_zb_stock_list():
    """
    Get all A but symbol start with '60' and '00' stock name list
    """
    if not os.path.exists(mainpath):
        os.makedirs(mainpath)
    df = ak.stock_zh_a_spot_em()
    df = df[df.代码.str.startswith(('60', '00',))]
    path = os.path.join(mainpath, f'a_zb_stock_list.csv')
    df.to_csv(path, encoding='utf-8')

def upsert_stock_detail(type: str, symbol: str, start_date: str, end_date: str = datetime.datetime.now().strftime('%Y%m%d'), period: str = 'daily'):
    """
    Update or download stock data by symbol. Today's data will be updated after closing.
    type: us | zh_a
    symbol: stock's code
    start_date: stock data's start date
    end_date: stock data's end date
    period: daily | weekly | monthly
    """
    dir = os.path.join(mainpath, f'{type}')
    if not os.path.exists(dir):
        os.makedirs(dir)
    path = os.path.join(dir, f'{symbol}.csv')
    # update if exists
    if os.path.exists(path):
        old_df = pd.read_csv(path)
        if old_df.shape[0] > 0: # if not empty
            start_date = str(int(old_df['datetime'].iloc[-1].replace('-', '')) + 1)
        else: # delete the file if empty
            os.remove(path)
        if int(start_date) > int(end_date):
            print(f'{symbol}, no update')
            return
        stock_data = eval('ak.stock_' + type + '_hist')(symbol=symbol, period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
        
        if stock_data.shape[0] < 1: # return 200 but without data
            print(f'{symbol}, no update')
        else:
            # update column name, because backtrader can't parse 'gbk' code.
            stock_data.columns=['datetime', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude', 'change', 'changeamount', 'turnoverrate']
            new_df = pd.concat([old_df, stock_data])
            new_df.to_csv(path, encoding='utf-8')
    else:
        stock_data = eval('ak.stock_' + type + '_hist')(symbol=symbol, period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
        if stock_data.shape[0] < 1: # return 200 but without data
            print(f'{symbol}, download success, but without data, maybe the stock exit.')
        else:
            stock_data.columns=['datetime', 'open', 'close', 'high', 'low', 'volume', 'turnover', 'amplitude', 'change', 'changeamount', 'turnoverrate']
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


def get_stock_list_task(stock_list: List[str], type: str, start_date: str, end_date: str = datetime.datetime.now().strftime('%Y%m%d'), period: str = 'daily'):
    # group's download bar
    bar = IncrementalBar('Download', max=len(stock_list))
    failed_num = 0
    for symbol in stock_list:
        try:
            upsert_stock_detail(type, symbol, start_date, end_date, period)
            bar.next()
        except Exception as e:
            print(f'cant download {symbol}, error: {e}')
            failed_num += 1
            bar.next()
    bar.finish()
    return len(stock_list) - failed_num

if __name__ == '__main__':

    type = 'zh_a'
    start_date='20020101'
    
    # get stock list when you download data first time.
    get_stock_list(type)

    # downlaod with multiple progress
    cpu_count = max(int(multiprocessing.cpu_count() - 2), 1)
    pool = multiprocessing.Pool(cpu_count)
    
    stock_list = name_list(f'{type}_stock_list.csv')
    # stock_list = stock_list[0:15]
    # total's bar
    pbar = tqdm(total=len(stock_list))
    # group per 20
    n = 20
    stock_lists = [stock_list[i:i + n] for i in range(0, len(stock_list), n)]
    def bar_update(num):
        pbar.update(num)
        print(f'{pbar.n} / {pbar.total} / {pbar.leave}')

    for stock_list in stock_lists:
        # get_stock_detail_task(bar, type, symbol, start_date, end_date, period)
        pool.apply_async(func=get_stock_list_task, args=(stock_list, type, start_date), callback=bar_update)

    pool.close()
    pool.join()
    pbar.close()
    print(f'download complete, success:{pbar.n}, failed:{pbar.total - pbar.n}')

    # download or udpate one stock
    # start_date='20220101'
    # end_date=datetime.datetime.now().strftime('%Y%m%d')
    # upsert_stock_detail('zh_a', '000001', start_date, end_date)
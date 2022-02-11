import os

import akshare as ak

mainpath = os.path.dirname(os.path.dirname(__file__)) + '../../datas/stock'

'''
获取股票数据
'''

def get_a_stock_list():
    """
    获取A股股票清单
    沪深京三个交易所
    """
    df = ak.stock_info_a_code_name()
    path = os.path.join(mainpath, f'a_stock_list.csv')
    df.to_csv(path)

def get_a_sh_stock_list(indicator: str = '主板A股'):
    """
    获取A股股票清单-上海证券交易所
    indicator="主板A股"; choice of {"主板A股", "主板B股", "科创板"}
    """
    df = ak.stock_info_sh_name_code(indicator=indicator)
    path = os.path.join(mainpath, f'a_sh_{indicator}_stock_list.csv')
    df.to_csv(path)

def get_a_sz_stock_list(indicator: str = 'A股列表'):
    """
    获取A股股票清单-深证
    indicator="A股列表"; choice of {"A股列表", "B股列表", "CDR列表", "AB股列表"}
    """
    df = ak.stock_info_sz_name_code(indicator=indicator)
    path = os.path.join(mainpath, f'a_sz_{indicator}_stock_list.csv')
    df.to_csv(path)

def get_a_bj_stock_list():
    """
    获取A股股票清单-北证
    """
    df = ak.stock_info_bj_name_code()
    path = os.path.join(mainpath, f'a_bj_stock_list.csv')
    df.to_csv(path)

def get_a_stock_detail(symbol: str, start_date: str, end_date: str):
    """
    获取每日后复权股票数据
    symbol: 股票代码
    start_date: 开始日期
    end_date: 结束日期
    """
    stock_data = ak.stock_zh_a_hist(symbol=symbol, period='daily', start_date=start_date, end_date=end_date, adjust='hfq')
    path = os.path.join(mainpath, f'{symbol}.csv')
    stock_data.to_csv(path, encoding='utf-8')

def name_list(csv_name):
    import csv
    csv_f = os.path.join(mainpath, f'{csv_name}')
    stock_list = []
    with open(csv_f, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['name'].startswith('N'):
                stock_list.append(row['symbol'])
            else:
                print(row['name'])
    return stock_list

def download_all_stock(csv_name):

    from progress.bar import IncrementalBar

    stock_list = name_list(csv_name)

    bar = IncrementalBar('Download', max=len(stock_list))
    new_stock_list = []
    for symbol in stock_list:
        bar.next()
        try:
            get_a_stock_detail(symbol)
        except KeyError:
            new_stock_list.append(symbol)

        bar.finish()

    if len(new_stock_list) > 0:
        print(f'新股票有: {new_stock_list}')


if __name__ == '__main__':
    
    get_a_stock_list()

    # download_all_stock('a_stock_list.csv')
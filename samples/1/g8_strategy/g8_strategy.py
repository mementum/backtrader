# use MA cross to buy/sell
import datetime
import backtrader as bt
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class MAStrategy(bt.Strategy):
  params = (
    ('ma_period1', 10),
    ('ma_period2', 60),
    ('price_period', 50)
  )

  def log(self, txt, dt=None):
    dt = dt or self.datas[0].datetime.date(0)
    # print('%s, %s' % (dt.isoformat(), txt))

  def __init__(self):
    self.buy_order = None
    self.sell_order = None
    self.trades = []

    # Add a MovingAverageSimple indicator
    self.ma1 = bt.indicators.SimpleMovingAverage(self.data, period=self.params.ma_period1)
    self.ma2 = bt.indicators.SimpleMovingAverage(self.data, period=self.params.ma_period2)
    self.highest = bt.indicators.Highest(self.data, period=self.params.price_period, subplot=False)
    self.isCrossUp = bt.indicators.CrossUp(self.ma1, self.ma2)

    data = pd.read_csv(f'{base_dir}/up_stat_week.csv', index_col='id', dtype={'id': np.character})
    self.stat = {
      'low': data.low['000001'],
      'middle': data.middle['000001'],
      'high': data.high['000001']
    }

  def notify_order(self, order):
    if order.status in [order.Submitted, order.Accepted]:
      # Buy/Sell order submitted/accepted to/by broker - Nothing to do
      return

    # Check if an order has been completed
    # Attention: broker could reject order if not enough cash
    if order.status in [order.Completed]:
      if order.isbuy():
        # self.log('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
        #     (order.executed.price,
        #      order.executed.value,
        #      order.executed.comm))

        self.buyprice = order.executed.price
        self.buycomm = order.executed.comm
      else:  # Sell
        pass
        # self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
        #          (order.executed.price,
        #           order.executed.value,
        #           order.executed.comm))
    elif order.status in [order.Canceled, order.Margin, order.Rejected]:
      self.log('Order Canceled/Margin/Rejected')

  def notify_trade(self, trade):
    if not trade.isclosed:
      return

    self.trades.append(trade)
    self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
             (trade.pnl, trade.pnlcomm))

  def next(self):
    if not self.position:
      if self.check_direction(self.ma2) > 0 and \
        self.is_cross_up() and \
        self.data.close[0] >= self.highest[0] and \
        self.get_percentage(self.data.close[0], self.data.open[0]) >self.stat['middle']:
        # buy 1
        # self.log('BUY CREATE, %.2f, Find high price at: %s, %.2f' % (self.data.close[0], self.data.datetime.date(0 - i).isoformat(), self.data.close[0 - i]))
        self.log('BUY CREATE, %.2f' % (self.data.close[0]))
        self.buy_order = self.buy()
    else:
      if not self.buy_order:
        print('Error.')
        return

      if self.data.close[0] >= self.ma1[0] * (1 + self.stat['high'] * 2 / 100): # rise too fast
        if self.data.close[0] < self.data.open[0] and \
          (self.get_percentage(self.data.close[-1], self.data.open[-1]) > self.stat['high'] or \
          (self.get_percentage(self.data.close[-1], self.data.open[-1]) > self.stat['middle'] and self.get_percentage(self.data.close[-2], self.data.open[-2]) > self.stat['middle'])):
          # sell 1
          self.sell_order = self.sell()
      elif self.is_dead_cross():
        # sell 2
        # self.log('SELL CREATE, %.2f' % close[0])
        self.sell_order = self.sell()

  def check_direction(self, line):
    if line[0] > line[-1] > line[-2]:
      return 1 # up
    elif line[0]  < line[-1] < line[-2]:
      return -1 # down
    else:
      return 0 #

  def is_cross_up(self):
    return self.isCrossUp[0] > 0 or self.isCrossUp[-1] > 0 or self.isCrossUp[-2] > 0

  def get_percentage(self, val1, val2):
    return (val1 - val2)/val2 * 100

  def is_golden_cross(self):
    return self.ma1[0] >= self.ma2[0] and self.ma1[-1] < self.ma2[-1]

  def is_dead_cross(self):
    return self.ma1[0] < self.ma2[0] and self.ma1[-1] > self.ma2[-1]

  def check_low_price(self):
    close = self.data.close[0]
    i = 0
    while self.data.datetime.date(0 - i) > self.startDate and self.data.close[0 - i] < close * self.params.price_times:
      i = i + 1

    if self.data.datetime.date(0 - i) > self.startDate:
      return True, i
    else:
      return False, 0

def test_one_stock(file):
  cerebro = bt.Cerebro()
  cerebro.broker.setcash(10000.0)
  cerebro.broker.set_coc(True)
  # cerebro.broker.setcommission(0.0005)
  cerebro.addsizer(bt.sizers.AllInSizer)
  cerebro.addstrategy(MAStrategy)

  stock_id = file.split('.')[1]

  data = bt.feeds.GenericCSVData(
      dataname=f'{base_dir}/../stock_data/{file}',
      name=stock_id,
      datetime=1,
      open=2,
      close=3,
      high=4,
      low=5,
      volume=6,
      dtformat=('%Y-%m-%d'),
      fromdate=datetime.datetime(2010, 1, 1),
      todate=datetime.datetime(2020, 1, 1)
  )
  cerebro.resampledata(data, timeframe=bt.TimeFrame.Weeks)
  start_value = cerebro.broker.getvalue()
  result = cerebro.run()
  return result[0].trades

if __name__ == '__main__':
  base_dir = os.path.dirname(__file__)
  files = os.listdir(base_dir + '/../stock_data')
  i = 0
  result = dict(id=[], profit=[], weeks=[], profit_per_week=[])
  stock_count = 0
  for file in files:
    stock_id = file.split('.')[1]
    if stock_id.startswith('3') or stock_id.startswith('4') or stock_id.startswith('8'):
      continue

    i += 1
    # if i > 5:
    #   continue

    print(f'Test {i}, {stock_id}')
    stock_count = i
    trades = test_one_stock(file)

    for t in trades:
      result['id'].append(f'{stock_id}-{t.ref}')
      result['profit'].append(round(t.pnlcomm, 2))
      result['weeks'].append(t.barlen)
      result['profit_per_week'].append(round(t.pnlcomm/t.barlen, 2))

  resultData = pd.DataFrame(result)
  resultData.to_csv('./ma_test_result_trades.csv')

  # summary
  profit_sum = np.sum(resultData['profit'])
  profit_avg = np.average(resultData['profit'])
  profit_per_week_avg = np.average(resultData['profit_per_week'])
  trade_count = len(resultData['profit'])
  earn_trade_count = len(np.extract(resultData['profit'] > 0, resultData['profit']))
  loss_trade_count = len(np.extract(resultData['profit'] < 0, resultData['profit']))
  max_earn = np.max(resultData['profit'])
  max_loss = np.min(resultData['profit'])
  total_cache_use = np.sum(resultData['weeks'])

  print('---------------------')
  print(f'{stock_count} stocks, {trade_count} trades. {earn_trade_count} earns, {loss_trade_count} losses')
  print(f'profit_sum: {profit_sum}')
  print(f'profit_avg: {profit_avg}')
  print(f'profit_per_week_avg: {profit_per_week_avg}')
  print(f'max_earn: {max_earn}')
  print(f'max_loss: {max_loss}')
  print(f'total_cache_use(weeks): {total_cache_use}')
  sns.relplot(data=resultData, x='id', y='profit')
  plt.show()
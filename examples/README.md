# Examples

Each script shows one part of backtesting with slim-backtrader. Each one runs
on its own from the repository root (`python examples/01_first_backtest.py`)
using the data in `datas/`, and none needs a network. The test suite runs
every one of them (`tests/test_examples.py`), so an example that stops
working fails the build rather than misleading its reader.

| script | what it shows |
|---|---|
| [01_first_backtest.py](01_first_backtest.py) | cerebro, a data feed, a strategy with indicators, orders, the result |
| [02_data_feeds.py](02_data_feeds.py) | CSV formats, column mapping, date windows, resampling, Yahoo files, pandas |
| [03_indicators.py](03_indicators.py) | built-in indicators, arithmetic on lines, custom indicators with `next` and `once` |
| [04_order_types.py](04_order_types.py) | market, close, limit, stop, stop-limit, trailing stop, expiry; an order's statuses |
| [05_brackets_and_oco.py](05_brackets_and_oco.py) | bracket orders (entry, stop-loss, take-profit) and one-cancels-other |
| [06_target_orders_and_sizers.py](06_target_orders_and_sizers.py) | `order_target_percent`, fixed and percent sizers, a volatility-based custom sizer |
| [07_commissions_and_slippage.py](07_commissions_and_slippage.py) | percentage and fixed commission, futures margin and multiplier, slippage, cheat-on-close |
| [08_analyzers.py](08_analyzers.py) | returns, Sharpe ratio, drawdown, trade statistics, SQN, yearly and monthly returns |
| [09_observers_and_plotting.py](09_observers_and_plotting.py) | observers (cash and value, trades, drawdown, a benchmark) and saving a chart |
| [10_optimization.py](10_optimization.py) | `optstrategy` over a parameter grid, ranking the runs by their analyzers |
| [11_portfolio_rotation.py](11_portfolio_rotation.py) | several stocks, momentum ranking, monthly rebalancing on a timer |
| [12_signals.py](12_signals.py) | strategies built from signals: long/short, long-only, a separate exit signal |
| [13_timeframes_and_replay.py](13_timeframes_and_replay.py) | daily and weekly data in one strategy; a weekly bar replayed as it forms |
| [14_options_pricing.py](14_options_pricing.py) | Black-Scholes, greeks, Black-76, American options on a tree, implied volatility |
| [15_options_covered_call.py](15_options_covered_call.py) | stock plus a short call, assigned at expiry with the stock delivered |
| [16_options_delta_hedging.py](16_options_delta_hedging.py) | `OptionGreeks` in a strategy: a long call hedged when its delta drifts |
| [17_options_rolling_puts.py](17_options_rolling_puts.py) | a protective put rolled monthly: `ModelOptionData`, strikes set at listing, cash settlement |
| [18_broker_and_engine.py](18_broker_and_engine.py) | short selling with interest, deposits and fund returns, cheat-on-open, the CSV writer |
| [19_options_cash_secured_put.py](19_options_cash_secured_put.py) | the wheel: cash-secured puts, assignment, then covered calls |
| [20_options_vertical_spread.py](20_options_vertical_spread.py) | a monthly bull call spread: a defined-risk structure, and why the short leg goes first |
| [21_options_book.py](21_options_book.py) | iron condors as combo orders under the `CashCovered` margin model, with portfolio greeks, per-structure results and P&L by greek |
| [22_options_chains.py](22_options_chains.py) | whole option chains: a 30-delta put sold monthly on three stocks, picked from each chain by delta |
| [23_options_collar.py](23_options_collar.py) | zero-cost protective collar: holding stock, financed put protection via covered call |
| [24_options_covered_strangle.py](24_options_covered_strangle.py) | covered strangle: stock holding combined with covered call and cash-secured put for enhanced yield |
| [25_options_stock_collar_chains.py](25_options_stock_collar_chains.py) | multi-stock portfolio with dynamic option chains: delta-selected collars and physical delivery |

`--plot` (or `--show` for 09) opens a chart where a display is available.
Example 09 always writes its chart to `examples/output/`, which git ignores.

`samples/` holds upstream's original sample programs, kept while they are
pruned. `examples/` is this fork's own set, written against the current API.

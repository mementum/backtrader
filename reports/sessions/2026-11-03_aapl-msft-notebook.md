# 2026-11-03 — A worked notebook on AAPL and MSFT, and the eight defects it found

## What was asked

A Jupyter notebook of worked examples on AAPL and MSFT, with prices from
`yfinance`: strategies with and without options, several stocks at once,
plots, built systematically so that every part of the package is covered.
Any problem found in the package while testing it was to be root-caused and
fixed in the code.

## What was built

`examples/notebooks/aapl_msft_walkthrough.ipynb`, 61 code cells and 52
markdown cells in 14 parts. Each part uses only what the parts before it
introduced:

1. data: download and cache, adjusted prices, `PandasData`,
   `YahooFinanceCSVData`, resampling, replay, filters;
2. indicators: the library, checks against pandas, `next()` against
   `once()` and `exactbars=1`, two custom indicators;
3. a first strategy;
4. every order type, brackets and OCO;
5. sizers and `order_target_*`;
6. the broker: commissions, slippage, cheat-on-close, short interest,
   cheat-on-open, fund mode;
7. analyzers, observers and plotting;
8. several stocks: timer rebalancing, momentum rotation, a pair trade;
9. signals, optimisation with a heat map, the CSV writer;
10. option pricing;
11. options on model feeds: covered call, protective put, the wheel, a bull
    call spread as a combo, a collar, `OptionGreeks`;
12. an options book: iron condors under `CashCovered`, quote fills,
    `PortfolioGreeks`, `StructureTrades`, `GreeksAttribution`;
13. whole chains: inspecting one, puts by delta on both stocks, a call
    overlay on a 50/50 portfolio, a delta-hedged short straddle;
14. a summary table of every strategy.

The suite compiles the notebook's code (`test_the_notebook_compiles`) but
cannot run it: it needs Yahoo Finance.

## How it was tested without Yahoo Finance

The session's network policy refused Yahoo's hosts
(`query1.finance.yahoo.com`, `query2.finance.yahoo.com`, `fc.yahoo.com`;
`CONNECT tunnel failed, response 403`), so no AAPL or MSFT price was ever
downloaded here. To test every cell anyway, a harness outside the repository
copied two of the repository's own real price files, `datas/nvda-1999-2014.txt`
and `datas/orcl-1995-2014.txt`, into the notebook's price cache under the
names NVDA and ORCL. It set `TICKERS`, `START`/`END` (2008–2014) and
`OPTIONS_START` (2012) through the notebook's parameters cell, and executed
the whole notebook with `nbclient`: 2026-11-03, 97.8 s, no errors, no
warnings, 16 figures. None of those outputs was committed; the notebook is
committed without outputs, and its numbers on AAPL and MSFT are still to be
produced by a run with network access.

## The defects it found

Each was fixed on its own branch, with a regression test shown red against
the unfixed code first; details in `reports/OPEN_ITEMS.md` under "Fixed,
unreleased" and in `changelog.txt`. The branches are stacked in this order
on `master` as of 2026-11-03 (`5a0df87`):

| branch | defect |
|---|---|
| `fix-filter-return` | `Filter.__call__` dropped `next()`'s result, so a filter could not remove a bar without preloading: `Renko` crashed with `preload=False` |
| `fix-renko-hilo` | a falling `Renko` brick had its high below its low |
| `fix-wrapper-lines` | `DataFilter` and `DataFiller` raised `IndexError` wrapping a feed with extra lines, such as `YahooFinanceCSVData` |
| `fix-cancel-submitted` | an order cancelled on the bar that created it was not cancelled: a market order filled |
| `fix-gross-leverage` | `GrossLeverage` reported `(value - cash) / value`: net, not gross, and not even that for futures. An API break: its `fund` parameter is gone |
| `fix-writer-datetime` | the CSV writer wrote the strategy's datetime as a raw date number |
| `fix-implied-vol-floor` | `implied_vol` returned 0.2 for a worthless option |
| `fix-observer-buffer` | in run-once mode every observer held twice its bars, the second half `NaN` |
| `notebook-aapl-msft` | the notebook, its compile test and these notes |

Seven of the eight came from upstream; the implied-volatility one is in
this fork's own options layer.

## Examined and found to be by design

Filed in `reports/DECISIONS.md` so they are not re-raised: a closing order's
`executed.value` is the cost it closed, not the proceeds; inside
`next_open()` indicators still show the bar that just closed; `add_cash`
lands on the broker's next cycle. A fourth was already there: `todate` as a
midnight datetime excludes that day's bar. The notebook explains all four
where they come up.

Two of the notebook's own first drafts were wrong, not the package. The
wheel sized its contracts once, at the start: by 2014 its cash-secured puts
needed more cash than the account had, and `CashCovered` correctly refused
ten of them. The fund-mode demo deposited cash and ordered on the same bar,
so the deposit sat idle. Both now size from the current account.

## Left open

- Running the notebook on AAPL and MSFT, which needs those three hosts added
  to the environment's allowed domains. Its outputs can then be committed;
  `test_the_notebook_compiles` allows outputs.
- Not covered by the notebook: trading calendars (`addcalendar`), time
  zones, `Chainer` and `RollOver`, real-quote option feeds
  (`OptionPandasData`, `PandasChainSource`) and the `btrun` CLI. Each has an
  example script or tests.

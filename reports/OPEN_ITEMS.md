# Open items

Places where the code does something other than what it should. Fixed entries
move out of this file; things that turn out to be deliberate move to
`DECISIONS.md`.

*Last updated: 2026-11-03*

## Open

*None as of 2026-10-29.*

## Fixed, unreleased

### GrossLeverage reported net exposure, and not even that for futures

*Found 2026-11-03, when the AAPL/MSFT notebook's pair trade reported an
average gross leverage of -0.01 while holding 40% long and 40% short; fixed
the same day.* `GrossLeverage.next` computed `(value - cash) / value`. That
is the invested fraction of a long-only stock book and nothing else:
- a short sale's proceeds raise cash, so shorts netted against longs;
- futures cash moves by the margin, so a contract counted its margin rather
  than its notional;
- in fund mode `value` was the per-share fund value, a different unit from
  cash.

It came from upstream. It now sums `abs(size) * close * mult` over the
broker's positions and divides by the account value, in every mode; the
`fund` parameter is gone. The tests are in `TestGrossLeverage` in
`tests/test_analyzers.py`; against the unfixed code, 3 of 4 failed (short,
long/short, futures). The long-only test passed, as it should.

### An order cancelled on the bar that created it went on to fill

*Found 2026-11-03, touring the order types in the AAPL/MSFT notebook; fixed
the same day.* `Strategy.buy()` hands a new order to `BackBroker.transmit`,
which queues it in `submitted` until `check_submitted` runs on the broker's
next cycle. `BackBroker.cancel` looked only in `pending`, so a cancel on the
creating bar returned `False` and changed nothing. The order was then
accepted. A market order filled; a limit order stayed live with status
`Accepted`; and the caller had no sign of it but the ignored return value.
It came from upstream. `cancel()` now also removes the order from
`submitted`. A combo leg cancelled there leaves its siblings to
`_exec_combos`, which already cancels every leg of a combo with a dead one,
so no leg fills. The tests are
`test_cancel_on_the_bar_that_created_the_order` and
`test_cancelling_one_new_combo_leg_cancels_the_combo` in
`tests/test_broker.py`; against the unfixed code, all 3 failed (the market
order had status `Completed`).

### Data wrappers could not wrap a feed with extra lines

*Found 2026-11-03, filtering a Yahoo CSV feed in the AAPL/MSFT notebook;
fixed the same day.* `DataFilter._load` and `DataFiller._copyfromdata`
copied `range(self.p.dataname.size())` lines into the wrapper, which has only
the seven standard ones, so any inner feed with more (`YahooFinanceCSVData`'s
`adjclose`, an option feed's `bid` and `ask`) raised
`IndexError: list index out of range` on the first bar. They now pair their
own lines with the inner feed's by alias in `_startinner`. The tests are
`test_data_filter_wraps_a_feed_with_extra_lines` and
`test_a_wrapped_feed_may_carry_extra_lines` in
`tests/test_filters_sizers.py`; against the unfixed code, all 3 failed.

### A falling Renko brick had its high below its low

*Found 2026-11-03, reading `Renko.next` while fixing the item above; fixed
the same day.* A brick falling from `top` to `bot` was written with
`low = top` and `high = bot`. It came from upstream. Rising bricks were
right. The test is `test_every_renko_brick_has_its_high_above_its_low` in
`tests/test_filters_sizers.py`, which failed against the unfixed code
(`assert 3579.0 == 3629.0`).

### A filter could not remove a bar without preloading

*Found 2026-11-03, building the AAPL/MSFT notebook; fixed the same day.*
A filter removes a bar by calling `data.backwards()` and returning `True`,
which `AbstractDataBase.load` reads as "fetch another". `Filter.__call__`, the
base of `Renko` and of any user filter, called `next()` and returned `None`,
so `load()` reported the removed bar as delivered. With `preload=True` the
preload loop calls `load()` again and nothing showed. With `preload=False` the
strategy was handed an empty buffer and `Cerebro._runnext` raised
`IndexError: array index out of range` on the first bar. `__call__` now
returns `next()`'s result. The tests are
`test_a_filter_returning_true_removes_the_bar` and
`test_renko_bricks_do_not_depend_on_preload` in
`tests/test_filters_sizers.py`; against the unfixed code, 4 of the 5 failed
(the preloaded case passed).

### An aborted run left its feeds' files open

*Found 2026-10-29, running the suite under `-W error::ResourceWarning`; fixed
the same day.* `Cerebro.runstrategies` stopped its data feeds only after a run
that finished. A parse error in a CSV feed, or an exception from a strategy,
left every feed it had started open, with its file: 15 `ResourceWarning`s
across `tests/test_chaos.py`. The feeds are now stopped in a `finally` when a
run does not finish; a `stop()` that fails as well is suppressed, so the
error that ended the run is the one raised. The tests are
`TestAnAbortedRunClosesItsFiles` in `tests/test_chaos.py`; against the unfixed
code, 3 of the 4 failed (the fourth checks the suppression). The whole suite
now runs clean under `-W error::ResourceWarning`.

### Data wrappers left their wrapped feed's file open

*Found 2026-10-29, running `tests/test_filters_sizers.py` under `-W error`;
fixed the same day.* `DataFiller` and `DataFilter` start the feed they wrap
themselves (`_startinner`), since cerebro never sees it, but nothing stopped
it. A feed that was not preloaded kept its CSV file open after the run, and
Python reported a `ResourceWarning`. Under `-W error` three tests failed, on
`master` as well: `test_real_bars_are_untouched`,
`test_data_filter_accepting_everything_matches_the_plain_feed` and
`test_data_filter_delivers_each_bar_once[False]`. Both wrappers' `stop()` now
stops the inner feed, as `Chainer` and `RollOver` already did. The tests are
`test_data_filter_closes_the_wrapped_feeds_file` and
`test_the_wrapped_feeds_file_is_closed`; against the unfixed code, 2 of the 3
failed (a preloaded feed closes its file after preloading).

### `exactbars=1` lost bars: crashes at a feed's end, wrong values when unaligned

*Found 2026-10-29, testing option settlement in every memory mode; fixed the
same day.* `exactbars=1` keeps each data line in a deque only as long as its
minimum period, and it failed in two ways:

- **The current bar was pushed out.** `load()` calls `forward()` to make room
  for the next bar before it knows whether one will come. In a deque exactly
  as long as the minimum period, that evicted the current bar. When the feed
  had none left, `backwards(force=True)` removed the empty slot and nothing
  remained, so `BackBroker._get_value` read an empty buffer:
  `IndexError: deque index out of range`. Data feeds now always take the one
  extra slot (`extrasize=1`) that resampled and replayed feeds already had.
- **A rewound bar was loaded past.** When a feed's next bar belongs to a
  later timestamp, cerebro rewinds it, to be delivered later. But `next()`
  re-delivers a buffered bar only while `len(self) < self.buflen()`, which is
  never true of a deque that short, so the feed loaded past the waiting bar.
  On top of that, `LineBuffer.rewind` could not move the index of a full
  QBuffer. Feeds now count the bars they rewind and re-deliver those first,
  and the line rewind forces its index. The run-once fill path keeps its
  line-level rewind, uncounted.

Measured on 2026-10-29 against unbounded buffers, comparing every bar's
indicators and every feed's bar:

| case | before | after |
|---|---|---|
| a feed ending early after a position | `IndexError` | identical |
| two feeds trading on different days | `IndexError` / `ValueError` | identical |
| a daily feed with its weekly resample | **silently different from 2006-01-16** | identical |
| a single feed, aligned feeds, a weekly replay | identical | identical |

The tests are `TestMemorySavingWithFeedsEndingEarly` and
`test_exactbars_1_sees_what_unbounded_buffers_see` in
`tests/test_cerebro.py`, and option settlement's mode matrix now includes
`exactbars=1`. Against the unfixed code, 7 of them failed.

### `PercentSizer` ignores the commission scheme

*Found 2026-10-29, while fixing the stock-like `mult` item; fixed the same day.*
`PercentSizer._getsizing` computes `cash / data.close[0] * percents / 100`
and never asks the `CommInfoBase` what a unit costs. With a ×100 multiplier
(an option) it asks for 100 times what the cash can pay for, and the order
comes back `Margin`. Reproduced on 2026-10-29: 50% of 10,000 cash at a price
of 2.00 sizes 2,500 units, which completes with `mult=1` and is rejected with
`mult=100`. It ignored a futures-like margin the same way. It now divides by
`comminfo.getoperationcost(1, price)` - the price for a stock, the price
times `mult` for an option, the margin for a futures contract - and
multiplies by `get_leverage()`, as `getsize` does. It still returns a
fractional size unless `retint`, so a plain stock sizes exactly as before.
`getsize` itself was not used because it always truncates to an integer.
The red runs on 2026-10-29: `assert [] == [13]` (the ×100 order refused)
and `assert [13] == [25]` (the futures margin ignored).

### A CSV feed cannot be given a file-like object

*Found 2026-10-29, writing the option settlement tests; fixed the same day.*
`GenericCSVData`'s docstring says `dataname` is "the filename to parse or a
file-like object", and `CSVDataBase.start` does handle an object with
`readline`. But `MetaCSVDataBase.dopostinit` names the feed from
`os.path.basename(dataname)` when no `name` is given, and that raises
`TypeError: expected str, bytes or os.PathLike object, not StringIO`.
Reproduced on 2026-10-29 with `bt.feeds.GenericCSVData(dataname=io.StringIO(...))`.
A file-like source is now named after its `.name` attribute when that is a
path (an open file), and left unnamed otherwise (a `StringIO`).
`TestFileLikeSources` in `tests/test_feeds.py` failed against the unfixed
code with that `TypeError`, for a `StringIO` and an open file alike. The
`name="csv"` workarounds in the options tests are gone.

### The plot showed no dates, and the wrong ones when made to

*Found and fixed 2026-10-29, when asked to modernise plotting.* Five defects
in `plot/`, each reproduced before it was fixed:

- **No date labels on any axis.** `Plot.plot` hid every axis's tick labels
  with `setp(ax.get_xticklabels(), visible=False)`, then re-showed the
  lowest axis's the same way. Current matplotlib regenerates tick labels on
  draw and keeps only `tick_params` state, so all of them stayed hidden. The
  label text was right ("2006-01-31 23:59"), just invisible.
- **Year 3975 for 2006.** On the `fmt_x_ticks=None` path,
  `locator.AutoDateFormatter` passed backtrader date numbers (counted from
  year 1) to matplotlib's `num2date` (counted from 1970 since matplotlib
  3.3). `732313.99` became `3975-01-04`. The tick *positions* came out
  plausible only because the locator made the same mistake in both
  directions.
- **Month ticks one bar early.** With session-end stamps (`23:59:59`), the
  first tick landed on 2006-01-31 (index 21) instead of 2006-02-01 (22).
- **Timezone ignored.** The cursor readout read `09:05` for a bar stored at
  09:05 UTC on a feed with `tz="America/New_York"`, instead of `04:05`.
- **Charts stacked.** A second `cerebro.plot()` drew onto the first chart's
  figure, because `pyplot.figure(0)` returns the existing figure: 4 axes
  instead of 2.

`tests/test_plot.py` pins all five. Run on 2026-10-29 against the code before
the fix: `7 failed, 2 passed`; the figure-stacking test, written once the
full suite exposed the bug, failed with `assert 4 == 2`. With the fix the
full suite gave 447 passed, 1 skipped (72 s).

### Stock-like commission schemes apply `mult` to P&L but not to cost or value

*Found and fixed 2026-10-29, while investigating options
(`sessions/2026-10-29_options-design.md`, experiment E1).* `CommInfoBase`'s
docstring says `mult` is the "multiplier applied to the asset for
value/profit". On the futures-like branch it was. On the stock-like branch
(`stocklike=True`), `getoperationcost`, `getvaluesize`, `getvalue` and
`getsize` ignored it, but `profitandloss` applied it, and
`BackBroker._execute` added that P&L to cash when a position closes.

Reproduced on 2026-10-29: `setcommission(mult=100, stocklike=True,
commtype=COMM_FIXED)`. Buy one unit at 2.00 and sell it at 4.00 on a 10,000
account. The opening took 2.00 of cash instead of 200, and `getvalue()` read
10000 / 10001 / 10002 while the position is open. When the position closed the
value jumped to 10200. The final number was right; everything before it was
wrong by the factor `mult`, and so were the margin dry run in
`check_submitted` and the sizing in `getsize`.

No test used a stock-like scheme with `mult != 1`; every existing `mult`
test is futures-like. `samples/commission-schemes` reaches the combination
with `--commtype perc --stocklike` (`--mult` defaults to 10). Its output was
identical before and after the fix on 2026-10-29, because it prints only
order events. The fix multiplies by `mult` in the
four stock-like branches, in the core rather than in an option-only class
(question 17 of the options report). It is recorded as an API break in
`changelog.txt`. Four regression cases in `tests/test_comminfo.py` failed
against the unfixed code on 2026-10-29 (`4 failed`) and pass with the fix.
They cover the methods directly, plus a long and a short (with `shortcash`
both on and off) run through the broker. Full suite afterwards: 437 passed,
1 skipped in 68 s.

Not changed, and arguably a separate question: a *percentage* commission
(`COMM_PERC`) is charged on `size * price` without `mult`, on both branches.

## Fixed in 2.2.0

### A test needing an optional package failed instead of skipping

*Found and fixed 2026-08-24, by the artefact job the CI work added.*
`test_numpy_arrives_only_when_hurst_is_built` asserts that numpy *arrives* in
`sys.modules` once `HurstExponent` is built, so it needs numpy installed. It
had no `pytest.importorskip`, unlike every one of its neighbours guarding an
optional package, so the subprocess it spawns raised `ImportError` and
`check=True` turned that into `CalledProcessError`.

Invisible in the documented development environment, where `pip install -e
".[dev]"` pulls in matplotlib and pandas and therefore numpy. It failed in the
one place the sdist's suite is meant to be runnable - an environment holding
the engine and pytest and nothing else, which is what a downstream packager
verifying the artefact has. Demonstrated red there before the fix: 1 failed,
426 passed, 8 skipped. Green after: 426 passed, 9 skipped.

The convention it broke is now written down in CLAUDE.md, and the CI job that
catches the next one is `build and verify artefacts`.

## Fixed in 2.1.0

### The `alias` directive was invisible to a static checker

*Found and fixed 2026-08-23, as the residue of the `frompackages` item below.*
`alias` builds a subclass per name and `setattr`s it into the defining module,
so a module referring to one of its own aliases referred to a name pyflakes
could not see: `TR` in `atr.py`, `ROC` in `momentum.py`, `RSI` three times in
`rsi.py`, and ten more listed in a module's own `__all__`.

**Substituting the canonical class name would have been wrong**, and the shape
of the trap is worth keeping: an alias is *not* the same object.
`RSI.__mro__` is `RSI -> RelativeStrengthIndex`, and `RSI_SMA` inherits from
`RSI`; rewriting `class RSI_SMA(RSI)` would have changed the class hierarchy.
For `TR` and `ROC` the values are identical either way, but the sub-indicator's
plot label and CSV header would have changed from `TR` to `TrueRange`.

Instead the thirteen aliases a module names itself are written out as what the
directive would have built - a subclass carrying the parent's docstring and its
`aliased` marker - and dropped from the parent's `alias` tuple. Verified rather
than assumed: a hand-written alias was compared attribute by attribute against
a generated one (`__module__`, `__doc__`, `__bases__`, `__mro__`, `aliased`,
`lines`, `params`, `plotinfo`, `plotlines`, `_indcol` registration) and matched
on every one, and the 339 public names of `bt.indicators` are identical
before and after, down to each one's module, `aliased` and MRO.

The directive is untouched and still used by the ~140 aliases no module names.

pyflakes over `backtrader/` now reports **no undefined name at all**, down from
15, and `test_pyflakes_finds_no_undefined_name_anywhere` fails the suite if one
comes back. What it still reports is the star-import re-exports every
`__init__.py` is built from, which are deliberate - see
`IMPROVEMENT_SUGGESTIONS.md`.


### `frompackages` defeated static analysis

*Found 2026-08-22, fixed 2026-08-23.* `packages` and `frompackages` import a
package when an object is constructed and `setattr` the names into the defining
module's globals — and into every base class's module besides. Names a reader
cannot see are names a checker cannot check: pyflakes reported **19 undefined
names** across `hurst.py`, `ols.py` and `calmar.py`, so it could not have seen
a genuine mistake anywhere in those files either.

All three now import what they use, visibly, at the point of use:

- `calmar.py` asked for `collections` and `math` — **stdlib**, with no
  optionality to preserve. Plain module-level imports.
- `hurst.py` (numpy) and `ols.py` (pandas, statsmodels) declare the names at
  module level and bind them in a small `_import*()` helper called from
  `__init__`, so the import still happens on first construction and raises a
  message naming the package and how to install it.

The count is **19 → 1**, and the one left is an alias in an `__all__`, listed
under *Open* above.

The invariant this protects is checked rather than asserted:
`TestNothingOptionalIsImportedEagerly` runs `import backtrader` in a fresh
interpreter and fails if numpy, pandas, statsmodels, matplotlib or requests
comes with it, and pins that numpy arrives exactly when a `HurstExponent` is
built. `TestInjectedNamesAreGone` fails if any module under `backtrader/`
declares the directive again, and runs pyflakes over the three.

The mechanism itself is kept — it is a documented extension point, and
`tests/test_metaclass.py::test_run` still exercises it through
`testcommon.SampleParamsHolder`. Nothing in the library uses it.

*Correction:* the original entry listed `factorial` among the injected names.
It is not in `backtrader/` at all; it is in `tests/testcommon.py`, which uses
the directive deliberately to test it.


### `DataFilter` delivered every bar twice when preloading

*Found and fixed 2026-08-23.* 510 bars for a 255-bar feed, each date twice.
`_load` asked `not len(dataname)` to mean "not started yet", but `len()` is
also 0 immediately after `home()` rewinds a preloaded feed - so preloading
restarted the source, reopened the file it had just closed, and read the whole
thing a second time. Both wrappers now start their inner feed from `start()`,
which runs once per run and means what it says.

The order check added the same day found this by itself: the duplicate run
showed up as bar 256 dated 2006-01-02, after 2006-12-29.

### `DataFiller` read the numeric `sessionend`

*Found and fixed 2026-08-23.* `datetime.combine(date, self.p.dataname.sessionend)`
raised `TypeError: combine() argument 2 must be datetime.time, not float`. On a
started feed the bare name is the numeric session end `_start_finish()`
computed; the `datetime.time` the user configured is `p.sessionend`. Both that
and the matching `sessionstart` are fixed.

Its output was then checked by hand rather than recorded from the code: given a
feed carrying 10:31 and 10:34 of one session, the filler inserts 10:32 and
10:33 priced at the 10:31 close, carrying the configured fill volume, and
leaves the real bars alone. `fill_price` overrides the close for inserted bars
only.

### `Position.set` reported nothing opened when opening from flat

*Found and fixed 2026-08-23.* The branch taken from a flat position read
`self.upopened = self.size` - the *old* size, always 0 there - where every
sibling branch, and `update()` for the same move, report the size opened.
It reads `size` now, and a test asserts the two agree.

### Two `Vortex` indicators existed, and the exported one was not the maintained one

*Found and fixed 2026-08-23.* `backtrader/indicators/vortex.py` and
`backtrader/indicators/contrib/vortex.py` held the same implementation.
`bt.indicators.Vortex` resolved to the contrib one, so an innocuous
`import backtrader.indicators.vortex` re-registered `Vortex` in
`MetaIndicator._indcol` and silently swapped which class the name meant.

The top-level module survives - it is the Black-formatted copy, and the contrib
one carried a duplicated copyright line from the licence sweep. It is imported
from `indicators/__init__.py` like every other indicator, and
`backtrader/indicators/contrib/` is gone: `vortex.py` was all it held, so the
package and the `import backtrader.indicators.contrib` line went with it.
`backtrader/studies/contrib/` is untouched.

### `PivotPoint`'s pivot line was unreachable by its own name

*Found and fixed 2026-08-23.* The line was called `p`, and `.p` on every
`LineIterator` is the params object. `LineSeries.__getattr__` is what forwards
an unknown name to `.lines`, and it only runs when normal lookup *fails* - so
the params instance attribute won, and the line could only be read as
`.lines.p`.

The line is `pivot` now, in `PivotPoint`, `FibonacciPivotPoint` and
`DemarkPivotPoint`. `linealias = dict(pivot="p")` keeps `.lines.p` returning
the same line object, so code using the only spelling that ever worked still
works. `.p` remains the params object, as it must.

### PandasData and the CSV feeds stamped the same bar differently

*Found 2026-08-22, fixed 2026-08-23.* The CSV feeds stamp a daily bar at the
session end; a DataFrame index carries a bare date, which lands on midnight.
The same session came out a day apart depending on which feed loaded it, and
feeding both into one cerebro misaligned them silently.

`PandasData` and `PandasDirectData` now apply the session-end convention, so
the two agree bar for bar. Only a bar with **no time of day at all** is moved,
and only when the timeframe is daily or coarser: intraday data, where midnight
is a real time rather than a missing one, is untouched. `sessionend` sets the
time, as it does for every other feed.


### A feed could go back in time and nothing said anything

*Found 2026-08-23, fixed the same day.* A source whose rows ran backwards, or
had one date out of place, loaded without a word, and every indicator, the
broker and every analyzer then computed against a timeline that never existed.

`AbstractDataBase.load()` now refuses a bar older than the one before it,
naming both dates and the bar number. Equal stamps are still accepted - tick
data routinely carries several ticks within the same second. The new
`checkorder` parameter (default `True`) turns it off for a source that
delivers its own ordering on purpose.

The check sees the raw source stream only: bars a filter produced come back
through `_fromstack()` and return before reaching it, so resampling and replay,
which move the clock about deliberately, are unaffected. `Chainer` already
enforced the same rule for itself, and `reverse=True` feeds reverse the file at
`start()`, so both were already in order.

Cost, measured 2026-08-23 by alternating both settings inside one process:
**+2.4%** of CPU on a bare feed load, **+0.7%** with ten indicators attached,
within noise in `next` mode.

### A NaN size or price was refused as a margin call

*Found 2026-08-23, fixed the same day.* `buy(size=float('nan'))` and a limit
order at a NaN price reached the broker intact, and the cash arithmetic turned
them into `Order.Margin` - NaN compares false against everything, so the
broker's `cash >= 0.0` test failed. The strategy was told the account was short
of money when it had in fact asked for something meaningless.

`OrderBase.__init__` now raises `ValueError` for a size that is `None`, NaN,
infinite or negative, and for a NaN or infinite `price`, `pricelimit`,
`trailamount` or `trailpercent`. These are programming errors rather than
market conditions, so they fail loudly instead of arriving as a notification
the strategy would have to guess the meaning of. A genuine funding shortfall
still reports `Order.Margin`.

*Correction to the entry this replaces:* it also claimed `buy(size=-5)` was
mislabelled. It is not. `Strategy.buy()` takes `abs(size)`, so that call buys
5 - and the `Margin` seen when the finding was written was real, 5 units at
~3600 against the default 10000 of cash. Size is a magnitude and the direction
comes from `buy()`/`sell()`; only the direct `broker.buy(size=-5)` path, which
bypasses that normalisation, is now refused.


### The Yahoo feed fabricated a volume for a row that had none

*Found and fixed 2026-08-23.* `feeds/yahoo.py` wrapped the volume field in a
bare `except: v = 0.0`, commented as covering a "null" volume. A null never
reached it - the loop at the top of the same method skips any row carrying one.
What it caught was a row too short to have a volume column, which it turned
into a silent zero, corrupting every volume-based indicator and sizer
downstream without a word.

Found by `tests/test_chaos.py`, which feeds the parser rows that are broken in
each of the ways a real file is.

### A truncated CSV row raised a bare `StopIteration`

*Found and fixed 2026-08-23.* Empty message, and the wrong type: StopIteration
is the iteration protocol's sentinel, so raising it from a parser means that
under PEP 479 any caller that is a generator turns it into a RuntimeError
instead. Nothing in the tree is such a caller today, which is the only reason
it had not bitten.

`CSVDataBase._load` now re-raises row-level failures as a `ValueError` naming
the file, the line and the row, with the original kept as `__cause__`. Every
CSV feed gained the line number, which none of them had: the old message was
`could not convert string to float: 'abc'` with no way to tell which of a
million rows was meant.

### Five bare `except:` clauses

*Found and fixed 2026-08-23.* Besides the Yahoo one above:
`lineseries.plotlabel` (now `AttributeError`), the `lineiterator` argument
probe (now `TypeError, ValueError`), the matplotlib backend switch (now
`Exception`) and the plot artist unwrap (now `TypeError, IndexError,
KeyError`). A bare `except:` swallows `KeyboardInterrupt`, `SystemExit` and
`MemoryError` along with everything else.

`tests/test_chaos.py` carries the mechanical check that keeps them out: the
package must contain no bare `except:` and must never catch `BaseException`.

### `Store.getdata` failed with `'NoneType' object is not callable`

*Found and fixed 2026-08-23.* A `Store` subclass that has not set `DataCls` or
`BrokerCls` got that message, which says nothing about the contract it missed.
Both now raise `NotImplementedError` naming the attribute. No class in the tree
subclasses `Store` any more - every store integration was deleted during the
slimming - so nothing had exercised it; it was at 33% coverage, now 73%.


### Concurrent cerebros clobbered each other's object cache

*Found and fixed 2026-08-23.* The cache behind `objcache` lived on the
`MetaIndicator` and `MetaLineActions` metaclasses — process-wide — and
`cerebro.run()` clears it and switches it on or off on every call. Two cerebros
running in different threads therefore reached into each other: a run declaring
`objcache=False`, executing alongside one using `objcache=True`, silently
received the other's cached indicator instances and built two indicators where
it had declared three.

The storage is thread-local now, and the logic both metaclasses had
copy-pasted is one class, `metabase.ObjectCache`.
`tests/test_concurrency.py` pins the interleaving that reproduces it rather
than leaving it to chance, and was demonstrated red against the unfixed tree.

### Optimization would have broken outright on Python 3.14

*Found and fixed 2026-08-23.* Python 3.14 removes pickle support from
`itertools`, and optimization pickles the cerebro to its workers. Four places
held an `itertools` object on something that gets pickled: `Cerebro._dataid`,
`Cerebro.stcount`, `Strategy._alnames` and `WriterFile._len`. All are plain
ints now.

`Cerebro.optstrategy` also stored its parameter combinations as a live
`itertools.product` iterator; it stores a list. That fixed a second defect
alongside the pickling one — the iterator was single-use, so a second `run()`
on an optimizing cerebro saw it exhausted.

The classifiers in `pyproject.toml` already advertise Python 3.14.

### `DataFilter` and `DataFiller` could not load a single bar

*Found and fixed 2026-08-23.* Both wrap another feed rather than filtering one
in place, and both raised `AttributeError: _tzinput` on the first bar. Nothing
hands the inner feed to cerebro, so nothing gave it an environment; and they
called the wrapped feed's `start()`, where only `_start()` reaches
`_start_finish()` — the half that sets `_tzinput` and the trading calendar.

Both now start the inner feed through a `_startinner()` helper. Two further
defects sit behind that one and are listed under *Open* above.

Nothing in the tree exercised either class, samples included; the
`data-filler` sample names them in its `--help` description but uses
`SessionFilter`/`SessionFiller`, which are different classes in `session.py`.

### `strategy.py` carried a corrupt shebang

*Found and fixed 2026-08-23.* `#!/usr/bin389/env python`. Harmless, since the
module is imported rather than executed, and the only such line in the tree.

## Fixed in 2.0.1

### The GPLv3 header was stripped from three shipped files

*Found and fixed 2026-08-23. Shipped broken in 2.0.0.*

`backtrader/brokers/__init__.py`, `backtrader/feeds/__init__.py` and
`backtrader/stores/__init__.py` lost their entire GPLv3 header block —
upstream's copyright line included — in commit `3359215` ("Remove integrations
that depend on abandoned packages"), which rewrote the import lists at the top
of each file and took the comment block with them. 2.0.0 was uploaded to PyPI
in that state.

This matters beyond tidiness: GPL-3.0 section 4 requires that the licence and
copyright notices be kept intact on every copy conveyed, and these files are
conveyed in both the wheel and the sdist. It also broke the rule CLAUDE.md
states outright — the header block stays, even during a mechanical sweep.

The headers are restored, and `tests/test_licensing.py` now fails if any
shipped file loses its notice again. That test was demonstrated red against the
pre-fix tree before the fix was kept.

Related, found in the same pass and fixed with it: no file said it had been
modified, which GPL-3.0 section 5(a) requires of a modified work, and the nine
fork-authored test modules carried no licence header at all.

## Fixed in 2.0.0

| item | fix |
|---|---|
| `tzparse('UTC')` raised `AttributeError` without pytz | resolved through stdlib `zoneinfo`; `_ZoneInfo` supplies `.localize()` |
| `AutoDict._close()` never closed the dict | `__setattr__` had `if False and key.startswith("_")`; the flag became a dict entry |
| `TimeFrame.getname(tframe)` crashed on its own default | `compression=None` reached `None > 1` |
| `filters.CalendarDays` unusable with its documented default | `fill_price=None` reached `> 0` before the branch that handles None |
| ~740k warnings per test run | `\*` in two docstrings (SyntaxWarning) and `datetime.utcnow()` (DeprecationWarning) |

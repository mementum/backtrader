# CLAUDE.md — slim-backtrader

*How to work in this repository. What the code *is*, read the code for. What is
here is what the code cannot tell you: which command to trust, what "done"
means, and which plausible-looking action is the wrong one.*

Items marked **(pending)** describe agreed plans that have not landed yet. When
one lands, delete the marker and the "as of" state around it.

---

## Project overview  **[core]**

A slimmed fork of [mementum/backtrader](https://github.com/mementum/backtrader):
a self-contained Python backtesting and live-trading library. It produces an
importable `backtrader` package plus a `btrun` console script — there is no app
and no service. Consumers are your own strategy code and anyone using the fork.

The project's purpose is *subtraction*: remove dead integrations, modernize aged
Python, speed up the core. A change is **done** when the full test suite is green,
the change advances one of those three goals, and any API break is recorded.

- **Primary language / runtime:** Python **3.13** (floor — see *Environment*)
- **Entry point:** there is none for the library. The command that exercises the
  whole thing is `pytest`, run from the repository root.
- **Central concept:** **lines objects built by metaclasses.** Every Indicator,
  Strategy, Data feed and Analyzer is a `LineSeries` whose class-level `lines`,
  `params`, `alias` and `plotinfo` declarations are turned into real machinery at
  class-creation time by `metabase.MetaParams` and `lineseries.MetaLineSeries`.
  Read `backtrader/metabase.py` and `backtrader/lineseries.py` before touching
  anything in the core; almost every surprising behaviour originates there.

## Environment  **[core]**

```bash
conda activate backtrader
```

- Environment definition: `environment.yml` at the repo root. Create the env with
  `conda env create -f environment.yml`. **The env is named `backtrader`** - the
  *distribution* is `slim-backtrader`, the env is not; keep the two apart. The
  personal env `/home/deh/miniforge3/envs/inv313` also carries an editable
  install of this repo — it is *not* the project env; do not run the suite
  there or document it.
- Install editable from the repo root: `pip install -e ".[dev]"`. The engine has
  **no runtime dependencies**; everything optional is an extra declared in
  `pyproject.toml` (`plotting`, `pandas`, `online`, `calendars`, `talib`, `options`, `dev`).
- **Python 3.13 is the floor.** Do not write code that must also run on an older
  interpreter, and delete compatibility shims on sight rather than preserving them.
- A fresh clone needs exactly two things: the conda env, and `pip install -e ".[dev]"`.
  Test fixtures live in `datas/` and are tracked, so the suite needs **no
  network, no credentials, no services and no secrets**. If a change introduces a
  requirement for any of those, that is a design problem in this project, not a
  setup step to document.
- `.idea/` is gitignored, says "Python 3.12", and is stale. Ignore it.

## Key conventions  **[core]**

The non-obvious ones — where a reasonable reader guesses wrong:

- `lines = ('sma',)`, `params = (...)` and `alias = ('SMA', ...)` are **class-level
  declarations consumed by metaclasses**, not plain attributes. Adding, renaming or
  reordering one changes the generated class. Read params as `self.p.<name>`, lines
  as `self.lines.<name>` / `self.l.<name>`, values as `self[0]`.
- **Aliases are public API.** `bt.indicators.SMA`, `SimpleMovingAverage` and
  `MovingAverageSimple` are one class registered under several names, and
  `mabase.MovingAverage` auto-registers every moving average into the `MovAv`
  namespace. Renaming a class silently removes names from `bt.indicators` without
  any import error at definition time.
- **Every indicator has two execution paths:** `next()` (bar-by-bar) and `once()`
  (vectorized, used when `runonce=True`). Fixing one and not the other passes half
  the matrix — `testcommon.runtest` runs every case across
  `runonce ∈ {True, False} × preload ∈ {True, False} × exactbars ∈ {-2, -1, False}`,
  so a one-sided fix surfaces as a mismatch in *some* combination, not all.
- **Indexing is relative to now**, not list semantics: `data.close[0]` is the
  current bar, `[-1]` the previous one.
- **`minperiod` is computed by the framework, not declared**, and the tests assert
  it (`chkmin`). If it moves, the change altered when the indicator becomes valid.
- **`cerebro.plot()` shows figures wherever the backend can** (since
  2026-10-29): a window from a script, inline in a notebook, nothing on `Agg`.
  matplotlib picks the backend; `tests/conftest.py` pins `MPLBACKEND=Agg` so the
  suite never opens a window or blocks. A test that plots must keep that pin,
  or pass `iplot=False`.
- **The plot's x axis is bar indices, not dates.** Backtrader's date numbers
  count from year 1 and matplotlib's from 1970; mixing them labelled 2006 as
  3975. Convert through `plot.locator.bars_to_mpl`, never `matplotlib.dates`
  on raw `datetime` line values.
- **The GPLv3 header block at the top of every file stays.** This is a GPL fork:
  keep upstream's copyright line and add to it — never replace or drop it, not
  even during a mechanical sweep.

---

## Scope: what a session may do without asking  **[core]**

Standing authorization, matching the README's stated aims:

- **Mechanical modernization.** The Python 2 layer is gone as of 2.0.0
  (2026-08-22); keep it that way. Fix deprecated stdlib calls on sight.
- **Delete dead integrations.** The known ones are gone (see
  `reports/DECISIONS.md`). A removal is finished only when **nothing in the tree
  references it** — including `__init__.py` exports, `btrun`, `samples/`, the
  README and `reports/`. Grep the whole tree.
- **Refactor internals** of the metaclass core and indicator bases for clarity or
  speed.

And what bounds it:

- **The public API may break freely** — that is the point of the fork — but every
  break is recorded in `changelog.txt` **in the same commit**. No deprecation shims.
- **One concern per branch.** A modernization sweep and a behaviour change never
  share a commit; a reviewer cannot see the second inside the diff of the first.
- **A performance claim needs a measurement**: the number, the command that
  produced it, and the date. "Faster" without numbers does not go in the changelog.

## Git workflow  **[core]**

- **`master` is protected, and the protection cannot be bypassed** (since
  2026-08-24). `CI passed` is a required status check, so a commit reaches
  `master` only once CI has gone green **on that exact SHA**. Pushing a fresh
  commit straight to `master` is rejected — it carries no checks, and none will
  ever arrive for it. Verified rather than assumed, on 2026-08-24:

  ```
  remote: error: GH013: Repository rule violations found for refs/heads/master.
  remote: - Required status check "CI passed" is expected.
   ! [remote rejected] master -> master (push declined due to repository rule violations)
  ```

  It is a **repository ruleset** (Settings -> Rules -> Rulesets), not a classic
  branch-protection rule, which is why the error says `GH013` and points at
  `/rules`. Look there, not under Settings -> Branches.
- Feature work happens on a **branch in the main checkout** — now because the
  protection requires it, not only by convention. No worktrees.

  ```shell
  git checkout -b <name>
  # work; commit
  git push -u origin <name>       # CI runs here
  # wait for `CI passed` to go green on the branch
  git checkout master
  git merge --ff-only <name>      # fast-forward preserves the SHA...
  git push origin master          # ...so the green checks come with it
  ```

  **The fast-forward is load-bearing.** A merge commit is a new SHA with no
  checks and is rejected; `--ff-only` fails loudly rather than creating one.
- Commit when asked. **Never push, never merge into `master`, never delete a
  branch** without an explicit instruction. The full commit→push→merge flow is
  *not* the default here.
- **Tags are not branches, and the protection does not cover them.** That is why
  `git push origin vX.Y.Z` still works — and why it is the one irreversible git
  action here. See *Versioning and release*.
- The remote is `origin` = `git@github.com:dennisdeh/backtrader-slim.git` (SSH).
  The GitHub repository was renamed from `backtrader`; the old URL still
  301-redirects, but that redirect dies the moment anything else claims the
  old name, so do not rely on it.
- **`upstream` = `https://github.com/mementum/backtrader.git` is configured.**
  It is dormant - see `reports/DECISIONS.md` before proposing a sync.
  Run `git remote -v` before diagnosing any push/fetch failure.
- **There is no PR workflow, and `gh` is not installed.** The protection needs
  no pull request — a green branch plus a fast-forward satisfies it. Repository
  settings and branch protection cannot be changed from a session at all: there
  is no token, and SSH does not authenticate the REST API.
- Read `git status` before staging; never `git add -A` from the repo root blind.

## Testing  **[core]**

- `pytest` from the repository root — **in the foreground, with a bounded
  timeout.** Do not background the runner or spawn polling loops.
- **698 tests, ~80 s** (2026-11-03, Python 3.13). `pytest --cov` adds
  coverage and takes ~4 min; coverage is 72% counting branches.
  **Report exact pass/fail counts.** "Tests pass" without numbers is not a
  report.
- The suite is offline and credential-free, and must stay that way.
- If you narrow a run to one module, **say so explicitly** — a silently narrowed
  run reads as a full one.
- **The indicator tests are golden-value regressions.** `chkvals` holds formatted
  values at three points (latest, first valid bar, midpoint) plus `chkmin`.
  Changing a golden value changes what the library computes. Never adjust one to
  make a test green: either the change was intended — then say so in the commit
  message and the changelog — or you have found a bug.
- **Every fix ships a regression test demonstrated to FAIL against the unfixed
  code.** Stash the fix, run the test, paste the red output. A test written after
  the fix and never seen red proves nothing.
- A new indicator or feature needs a test in the existing style
  (`tests/test_ind_<name>.py`). Running `python test_ind_<name>.py` directly prints
  the expected block via `main=True` — but **that generator blesses whatever the
  implementation currently does**. Verify the values against the formula by hand
  before pasting them in.
- **Root-cause discipline:** when correcting an expectation or a literal, grep the
  *whole* tree for the same value before declaring it fixed — sibling test files
  duplicate expectations (`rg -n "<value>" tests/`).
- **CI runs on GitHub Actions** (`.github/workflows/ci.yml`, since 2026-08-24):
  black, the suite on 3.13/3.14 × Linux/macOS/Windows, coverage with a floor,
  and an artefact build that installs the sdist and the wheel and checks both.
  It is not a reason to skip the local run — **run `pytest` before you claim a
  change works**; CI is what stops an unrun suite reaching `master`, several
  minutes later.
- **A test that needs an optional package uses `pytest.importorskip`.** The
  sdist ships the suite for downstream packagers, whose environment has the
  engine and pytest and nothing else; a hard import there is a failure, not a
  skip. CI's artefact job is what catches it.
- **The suite is warning-free and must stay that way.** `filterwarnings` in
  `pyproject.toml` turns backtrader's own `DeprecationWarning`s and any
  `SyntaxWarning` into errors, so a new warning fails the run rather than
  joining a pile of 740k the way it used to.

## Debugging  **[core]**

- **State the root cause with evidence — a log, a reproducing command, or a
  failing test — before editing code.** A patch without a stated cause is a guess
  with a diff attached.
- **Check `examples/` and `samples/` before writing a reproduction.**
  `examples/` (this fork's own, run by `tests/test_examples.py`) and the 68
  upstream programs in `samples/` exercise most code paths; a bug reported
  against strategy code usually already has one.
- **An API change that breaks an example fails the suite.** Update the
  example in the same commit; `examples/` is documentation that runs.
- **A scoped grep answers a scoped question.** "Who references this?" is a
  whole-tree question — `samples/`, `contrib/`, `tools/` and the README included.
- Do not treat a prior session's "already fixed" list as an exclusion list. It is
  a point-in-time record, stale by construction. Judge every path on today's source.

## Formatting  **[core]**

- **Black (88 columns) is the formatter**, configured in `pyproject.toml`
  (`target-version = py313`). The one-off sweep across `backtrader/` landed on
  2026-08-22 (167 files); **there should never be a second wholesale reformat.**
- From here, run Black on the files a task modifies — not on the tree.
- `samples/`, `contrib/` and `tools/` are excluded on purpose: they are upstream
  material being pruned, and reformatting them would bury the removals in noise.
  `tests/` is not excluded but was not swept; it converges file by file.

## Versioning and release  **[core]**

- **Plain semver, `X.Y.Z`. The current release is `2.2.0`** (2026-08-24).
  Upstream's `X.Y.Z.I` scheme — where `I` counted the built-in indicators — is
  **retired**; the fourth digit is gone, and `__btversion__` in
  `backtrader/version.py` is a 3-tuple, derived from `__version__` — bumping the
  string is the whole change.
- Bump the version **only when asked**.
- **The distribution is `slim-backtrader`; the import package is `backtrader`.**
  PyPI's `backtrader` is upstream's and can never be reused. `pip install
  backtrader` installs upstream, not this fork - and the two cannot coexist.
  Release steps are the README's *Releasing* section.
- **Never push a tag.** A `vX.Y.Z` tag on `origin` runs
  `.github/workflows/release.yml`, which uploads to PyPI, and **a version can
  never be uploaded twice**. Tagging is the release; it needs the same explicit
  instruction a push does, and it is the one git action here that cannot be
  undone.
- **Never run `twine upload`, `pypi.sh`, or `setup.py bdist_wheel` for
  release.** Publishing is not an agent action, by hand or by tag.
- Publishing uses PyPI **trusted publishing** (OIDC), so there is no API token
  in the repository and none to hand out. If an upload fails on credentials,
  the fix is on PyPI's publisher settings, not in a secret.
- `changelog.txt` is the change record: append notable changes, and always
  API breaks.

---

## Documentation  **[core]**

`reports/` holds documentation that **aggregates across modules** - a small,
fixed set of files, each answering exactly one standing question. Point-in-time
records go in `reports/sessions/`.

| the fact | the file |
|---|---|
| the code does something other than what it should | `reports/OPEN_ITEMS.md` |
| the code is correct and could be better | `reports/IMPROVEMENT_SUGGESTIONS.md` |
| examined, found correct, not to be re-raised | `reports/DECISIONS.md` |
| what is tested, how it is selected, what it costs | `reports/TESTING_SUITE.md` |
| which part owns what, and what flows between them | `reports/ARCHITECTURE.md` |
| what happened in one piece of work | `reports/sessions/YYYY-MM-DD_<slug>.md` |
| what changed in a release, and every API break | `changelog.txt` |

- **Do not add a new file to `reports/` without asking.** That is how a reports
  folder reaches 77 files. Update the existing one.
- `OPEN_ITEMS` vs `IMPROVEMENT_SUGGESTIONS` is *"is something wrong?"*, not *"is
  something worth doing?"*. A finding that turns out to be by design moves to
  `DECISIONS.md` **with its reasoning**, so the next session does not reopen it.
- **A new session report adds its own row to `reports/README.md`** in the same
  commit, using the report's own title as the row text.
- **Every document carries its vintage**: `*Last updated: YYYY-MM-DD*`,
  refreshed when **its** content changes. Session reports are exempt - they are
  dated by filename.
- **End a session by filing what is left.** A summary in the chat is not filing.
- **Update the existing file; do not create a parallel one.** State a fact once.
- **Anchor to symbol names, never line numbers** - in code comments too.
- **Date every measurement.** "2026-08-22: 254 passed, 69% coverage" stays
  checkable; a bare number does not.
- **Never write branch or merge state as present tense.** Give the date instead.
- **Search `reports/` before starting an investigation** - then check its
  vintage before trusting it.

### Where prose lives: docs, not code comments

**A code comment says *what* and points; `reports/` says *why*, with the
evidence.** Measurements, dated incidents, upstream contracts and the reasoning
behind a constant belong in the reports.

- **Keep in the code:** what the value is, the one-sentence trap, the pointer.
- **Move to reports:** the measurement and its date, the incident, what it cost.
- **Never delete a comment that records a defect or a measurement** - relocating
  is the only acceptable way to shorten it.
- **Do not number steps** (`# 0.1: ...`) - the numbers drift. **Do not restate
  the next line.** This codebase inherits upstream's long explanatory
  docstrings; leave them where they are correct.

## Housekeeping  **[situational]**

The root was cleaned on 2026-08-22. `optbinning/` (a separate project, 276
unversioned files), `create_coolercontrol_udev_rules.sh` and two root-owned
`.csm_setup_*` files were **moved**, not deleted, to
`../_moved_out_of_backtrader/`; the stale `build/` tree was deleted outright as
regenerable output.

**Keep the root clean.** Unrelated material does not live in this repository. If
something unexplained appears there, move it out and say so — do not delete
unversioned files, and do not `git add -A` from the root without reading
`git status` first.

---

## Rules vs. checks — how to grow this file

In order of value:

1. **A mechanical check** — a lint rule, a pre-commit hook, a test. Every check
   should exist because a defect got through.
2. **A rule in this file**, when a check is impossible or not yet worth writing.
3. **Nothing.** A rule nobody follows is worse than no rule: it trains the reader
   that this file is decoration.

**Keep this file about *how to work here*, not *what the code is*.** Anything an
agent can learn by reading the code belongs in the code.

**Prune as well as add.** Delete a rule when its check exists, when the subsystem
it guards is gone, or when it has never once been the thing that went wrong.

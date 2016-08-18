PyFolio Overview
################

Quoting from the main ``pyfolio`` page at http://quantopian.github.io/pyfolio/::

  pyfolio is a Python library for performance and risk analysis of financial
  portfolios developed by Quantopian Inc. It works well with the Zipline open
  source backtesting library

And now it works also well with *backtrader*. What's needed:

  - ``pyfolio`` obviously
  - And its dependencies (things like ``pandas``, ``seaborn`` ...)

    .. note::

       During the integration with version ``0.5.1``, an update to the most
       recent packages of the dependencies was needed, like ``seaborn`` from
       the previously installed ``0.7.0-dev`` to ``0.7.1``, apparently due to
       the absence of the method ``swarmplot``

Usage
*****

  #. Add the ``PyFolio`` analyzer to the ``cerebro`` mix::

       cerebro.addanalyzer(bt.analyzers.PyFolio)

  #. Run and retrieve the 1st strategy::

       strats = cerebro.run()
       strat0 = strats[0]

  #. Retrieve the analyzer using whatever name you gave to it or the default
     name it will be given to it: ``pyfolio``. For example::

       pyfolio = strats.analyzers.getbyname('pyfolio')

  #. Use the analyzer method ``get_pf_items`` to retrieve the 4 components
     later needed for ``pyfolio``::

       returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

     .. note::

	The integration was done looking at test samples available with
	``pyfolio`` and the same headers (or absence of) has been replicated

  #. Work with ``pyfolio`` (this is already outside of the *backtrader*
     ecosystem)

Some usage notes not directly related to *backtrader*

  - ``pyfolio`` automatic plotting works outside of a *Jupyter Notebook*, but
    **it works best** inside

  - ``pyfolio`` data tables' output seems to barely work outside of a *Jupyter
    Notebook*. It works inside the *Notebook*

The conclusion is easy if working with ``pyfolio`` is wished: **work inside a
Jupyter Notebook**


Sample Code
***********

The code would look like this::

  ...
  cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
  ...
  results = cerebro.run()
  strat = results[0]
  pyfoliozer = strat.analyzers.getbyname('pyfolio')
  returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
  ...
  ...
  # pyfolio showtime
  import pyfolio
  pf.create_full_tear_sheet(
      returns,
      positions=positions,
      transactions=transactions,
      gross_lev=gross_lev,
      live_start_date='2005-05-01',  # This date is sample specific
      round_trips=True)

  # At this point tables and chart will show up


Reference
=========

Look into the :doc:`../analyzers-reference` for the ``PyFolio`` analyzer and which
analyzers it uses internally

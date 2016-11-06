Writer
######

Write out to a stream the following contents:

  - csv stream with data feeds, strategies, indicators and observers

    Which objects actually go into the csv stream can be controlled with the
    ``csv`` attribute of each object (defaults to True for ``data feeds`` and
    ``observers`` / False for ``indicators``)

  - A summary of the properties of

    - Data Feeds
    - Strategies (lines and parameters)
    - Indicators/Observers: (lines and parameters)
    - Analyzers: (parameters and analysis outcome)

There is only a single Writer defined called ``WriterFile``, which can be added
to the system:

  - By setting the ``writer`` parameter of cerebro to True

    A standard ``WriterFile`` will be instantiated

  - By calling Cerebro.addwriter(writerclass, \*\*kwargs)

    ``writerclass`` will be instantiated during backtesting execution with the
    givenn ``kwargs``

    Given that a standard ``WriterFile`` does not ouput ``csv`` as a default,
    the following ``addwriter`` invocation would take care of it::

      cerebro.addwriter(bt.WriterFile, csv=True)

Reference
=========

.. currentmodule:: backtrader

.. autoclass:: WriterFile

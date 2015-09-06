
Data Resampling
###############

When data is only available in a single timeframe and the analysis has to be
done for a different timeframe, it's time to do some resampling.

"Resampling" should actually be called "Upsampling" given that one goes from a
source timeframe to a larger time frame (for example: days to weeks)

"Downsampling" is not yet possible.

``backtrader`` has built-in support for resampling by passing the original data
through a filter object which has intelligently been named: ``DataResampler``.

The class has two functionalities:

  - Change the timeframe

  - Compress bars

To do so the ``DataResampler`` uses standard ``feed.DataBase`` parameters during
construction:

  - ``timeframe`` (default: bt.TimeFrame.Days)

    Destination timeframe  which to be useful has to
    be equal or larger than the source

  - ``compression`` (default: 1)

    Compress the selected value "n" to 1 bar

Let's see an example from Daily to weekly with a handcrafted script::

  $ ./resampling-example.py --timeframe weekly --compression 1

The output:

.. thumbnail:: ./resample-daily-weekly.png

We can compare it to the original daily data::

  $ ./resampling-example.py --timeframe daily --compression 1

The output:

.. thumbnail:: ./resample-daily-daily.png

The magic is done by executing the following steps:

  - Loading the data as usual

  - Feeding the data into a ``DataResampler`` with the desired

    - timeframe
    - compression

The code in the sample (the entire script at the bottom).

.. literalinclude:: ./resampling-example.py
   :language: python
   :lines: 38-57

A last example in which we first change the time frame from daily to weekly and
then apply a 3 to 1 compression::

  $ ./resampling-example.py --timeframe weekly --compression 3

The output:

.. thumbnail:: ./resample-daily-weekly-3.png

From the original 256 daily bars we end up with 18 3-week bars. The breakdown:

  - 52 weeks

  - 52 / 3 = 17.33 and therefore 18 bars

It doesn't take much more. Of course intraday data can also be resampled.

The sample code for the resampling test script.

.. literalinclude:: ./resampling-example.py
   :language: python
   :lines: 21-

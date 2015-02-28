###############
Advanced Topics
###############

*****************
Platform concepts
*****************




************
Line Concept
************

The platform is designed around the "line" concept, possibly better explained with a concrete example:

  The series of "close" prices of a stock define a "line" conceptually and when drawn on a board and the points are joined together.

This is for sure not a disruptive innovation (many other software) packages have done it before, it is simply what everything revolves around.

As such most of the objects that play a role in the platform have 1 or more lines.

It is for sure best to first explain what the usual lifecycle of a line is:

  - Starts with length 0 ie: len(lineobject) == 0

  - Grows on each iteration of the platform by 1 item (operation *forward*)

  - Gets a value set at *index 0* and the value at *index 0* and previous ones (-1, -2, ...) may be read by other actors to create other values

Sometimes a line undergoes extra operations:

  - home. This one resets the *index 0* of the line without touching the underlying content.

    If a line already has a set of 500 values they remain there. This is useful to preload a series of data (closing prices for example) before doing calculations on them (indicators, strategies)

  - advance. Advances the logical *index 0* over existing data (used obviously after "home")

  - rewind. Moves the *index 0* backwards and reduces the buffer size.

    Useful if a data is being loaded which must be discarded.

 In fact a "line" is a wrapper around any kind of Python iterable modifying the access indices to have an *index 0* which is the current get/set point and keeping the pythonic notion of "last" because *-1* pulls the last set value before the current one.

In the platform most lines hold floating point (double precision) values, but lists and collections.deque can also be used to hold complex objects like Python datetime.datetime instances.

******************
LineSeries Concept
******************

A "line" is of not much help given that real life "objects" (like the OHLC price action daily summary of a security) has more than 1 line. Hence the "LineSeries"

These objects are capable of holdinde 1 or more lines in an array manner. There are three different ways to access line values for all objects derived from LineSeries:

  - object[line_index][value_index]

    This recalls a matrix

  - object.lines[line_index][value_index]

    This exposes the "lines" array which gives access to the lines

  - object.line_alias[value_index]

    Although not yet mentioned, lines have "aliases" to access them

LineSeries (and derived clases) feature the following syntax to define lines::

  class MyLineSeries(LineSeries):

      lines = ('alias1', 'alias2', 'alias3')

With that syntax 3 lines and the corresponding aliases have been created. Furthermore and when it comes down to inheritance::

  class MyLineSeriesSub(MyLineSeries):

      lines = ('alias4',)

Although it may not seem obvious at first ... MyLineSeriesSub HAS 4 lines. The 3 defined by its parent and the 4th one defined by itself.

.. note:: Python tuples and commas

   If a single line is defined, you need the sintactic comman at the end, to ensure standard Python tuple parsing does not interpret the string as an iterable itself creating lines with the following aliases: a, l, i, a, s, 4.

All the work needed to define the lines and control the inheritance is done in the background with MetaClasses before any object is instantiated.

The above example have defined lines which hold floating point values. To define a line that can hold complex objects do the following::

  class MyLineSeries(LineSeries):

      lines = ('alias1', ('alias2', 'ls'), 'alias3')

The line with *alias2* will uses a list to store values and can therefore store any complex object.


LineSeries and Parameters
-------------------------
Parameters definition is not strictly limited to LineSeries, but LineSeries and descendants do already feature the needed machinery to define parameters (other non LineSeries objects like a *Broker* also make use of the Params machinery)

Parameters work as follows (extending the above examples)::

  class MyLineSeries(LineSeries):
      lines = ('alias1', ('alias2', 'ls'), 'alias3')

      params = ((param1, default1), (param2, default2),)

Just like with lines, parameters are defined with a tuple, where each element is a tuple itself containing the name and default value.

Parameters are bound to "keyword arguments" (yes the **kwargs in function/method definitions). And as such the following changes the value of some of the parameters defined above::

  myls = MyLineSeries(param2=27)

In order to achieve this, there is no need to parse anything or even have a **kwargs in the __init__ definition. Most of the objects in the platform have an __init__ function like this::

  class MyLineSeries(LineSeries):
      lines = ('alias1', ('alias2', 'ls'), 'alias3')

      params = ((param1, default1), (param2, default2),)

      def __init__(self):
          # perform some actions
	  pass

Accessing the parameters inside a MyLineSeries instance is done with the synxtax seen below::

  class MyLineSeries(LineSeries):
      lines = ('alias1', ('alias2', 'ls'), 'alias3')

      params = ((param1, default1), (param2, default2),)

      def __init__(self):
          if self.params.param2 == 52:
	      print '52'
	  else:
	      print 'It is not 52'

Talking about inheritance again::

  class MyLineSeriesSub(MyLineSeries):
      lines = ('alias4',)

      params = ((param3, default3),)

      def __init__(self):
          if self.params.param2 == 52:
	      print '52'
	  else:
	      print 'It is not 52'

Params just like line are inherited and therefore *MyLineSeriesSub* has:

  - 4 lines (3 from parent + 1 newly defined)
  - 3 parameters (2 from parent + 1 newly defined)

MetaClasses do once again articulate all the work in the background for parameters.

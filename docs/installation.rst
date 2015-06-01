Installation
############

Requirements and versions
*************************

Basic requirements are:

  - Python >= 2.7.5
  - six

Additional requirements if plotting is wished:

  - Matplotlib >= 1.4.1

    It may work with previous versions, but this the one used for
    development

Python 3.x compatibility
========================

Every attempt has been made to remain cross-compatible with 2.7.x and
3.x by also using the six module as needed.

At the time of writing Python 3.x was long untested. It will need some
checking to assure that Python 3.x is supported.

.. note:: The latest tests were run with 3.4 and the platform run
	  smoothly but slower

There are different ways to install and use **backtrader**.

Install from pypi
*****************
For example using pip::

  pip install backtrader

*easy_install* with the same syntax can also be applied

Install from pypi (including *matplotlib*)
******************************************

Use this if plotting capabilities are wished::

  pip install backtrader[matplotlib]

This pulls in matplotlib which will in turn pull in other dependencies.

Again you may prefer (or only have access to ...) *easy_install*

Install from source
*******************

First downloading a release or the latest tarball from the github site:
https://github.com/mementum/backtrader

And the running the command::

  python setup.py install

Run from source in your project
*******************************

Again download a release or the latest tarball from the github site:

  https://github.com/mementum/backtrader

And then copy the *backtrader* package directory to your own project. Under a
Unix-like OS for example::

  tar xzf backgrader.tgz
  cd backtrader
  cp -r backtrader project_directory

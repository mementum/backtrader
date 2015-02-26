************
Installation
************
There are different ways to install and use **backtrader**.

Install from pypi
-----------------
For example using pip::

  pip install backtrader

*easy_install* with the same syntax can also be applied

Install from pypi (including *matplotlib*)
------------------------------------------
Use this if plotting capabilities are wished::

  pip install backtrader[matplotlib]

Again you may prefer (or only have access to ...) *easy_install*

Install from source
-------------------
First downloading a release or the latest tarball from the github site: https://github.com/mementum/backtrader

And the running the command::

  python setup.py install


Run from source in your project
-------------------------------

Again download a release or the latest tarball from the github site: https://github.com/mementum/backtrader

And then copy the *backtrader* package directory to your own project. Under a Unix-like OS for example::

  tar xzf backgrader.tgz
  cd backtrader
  cp -r backtrader project_directory

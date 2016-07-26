#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from collections import OrderedDict

import sys

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.nodes import nested_parse_with_titles

from backtrader import Indicator, Strategy, AutoInfoClass
try:
    from backtrader.talib import _TALibIndicator
except ImportError:
    _TALibIndicator = None
    pass  # will not work in readthedocs

import backtrader.feed as feed


PY2 = sys.version_info.major == 2

if PY2:
    string_types = str, unicode
else:
    string_types = str,


class BacktraderRef(nodes.General, nodes.Element):
    pass


class BacktraderRefDirective(Directive):
    RefCls = None
    RefPlot = True
    RefName = '_indcol'

    def run(self):
        indnode = []
        refattr = getattr(self.RefCls, self.RefName, {})
        for indname in sorted(refattr.keys()):
            # indnode.append(nodes.section())

            indcls = refattr[indname]

            # Title section (indicator name)
            indname = indcls.__name__
            indtitle = nodes.subtitle(indname, indname)
            indnode.append(indtitle)

            # Get the docstring and prepare it for parsing
            # a list is returned
            indclsdoc = indcls.__doc__ or ''  # __doc__ could be None
            inddoc = prepare_docstring(indclsdoc)

            # Alias section
            indaliases = getattr(indcls, 'alias', [])
            if indaliases:
                inddoc.insert(0, u'Alias:')
                purgedaliases = []
                for indalias in indaliases:
                    if not isinstance(indalias, string_types):
                        indalias = indalias[0]
                    purgedaliases.append(indalias)
                aliastxt = u'  - %s' % ', '.join(purgedaliases)
                inddoc.insert(1, aliastxt)
                inddoc.insert(2, u'')

            # Lines section
            indlines = indcls.lines._getlines()
            if indlines:
                inddoc.append(u'Lines:')
                for i, indline in enumerate(indlines):
                    inddoc.append(u'  - %s' % indcls.lines._getlinealias(i))

            # Params section
            indparams = indcls.params._getpairs()
            if indparams:
                inddoc.append(u'Params:')
                for pkey, pvalue in indcls.params._getitems():
                    try:
                        if issubclass(pvalue, self.RefCls):
                            pvalue = pvalue.__name__
                    except:
                        pass

                    inddoc.append(u'  - %s (%s)' % (pkey, str(pvalue)))

            if self.RefPlot:
                # Plotinfo section
                # indplotinfo = indcls.plotinfo._getpairs()
                if len(indcls.plotinfo._getpairs()):
                    inddoc.append(u'PlotInfo:')
                    for pkey, pvalue in indcls.plotinfo._getitems():
                        inddoc.append(u'  - %s (%s)' % (pkey, str(pvalue)))

                # PlotLines Section
                if len(indcls.plotlines._getpairs()):
                    inddoc.append(u'PlotLines:')
                    for pkey, pvalue in indcls.plotlines._getitems():
                        if isinstance(pvalue, AutoInfoClass):
                            inddoc.append(u'  - %s:' % pkey)
                            for plkey, plvalue in pvalue._getitems():
                                inddoc.append(u'    - %s (%s)' % (plkey, plvalue))
                        elif isinstance(pvalue, (dict, OrderedDict)):
                            inddoc.append(u'  - %s:' % pkey)
                            for plkey, plvalue in pvalue.items():
                                inddoc.append(u'    - %s (%s)' % (plkey, plvalue))
                        else:
                            inddoc.append(u'  - %s (%s):' % pkey, str(pvalue))

            # create the indicator node, add it to a viewlist and parse
            indsubnode = nodes.container()
            inddocview = ViewList(inddoc, indname)
            nested_parse_with_titles(self.state, inddocview, indsubnode)

            # Add the indicator subnode to the list of nodes to be returned
            indnode.append(indsubnode)

        return indnode


class IndRef(BacktraderRef):
    pass


class IndRefDirective(BacktraderRefDirective):
    RefCls = Indicator
    RefPlot = True


class DataBaseRef(BacktraderRef):
    pass


class DataBaseRefDirective(BacktraderRefDirective):
    RefCls = feed.DataBase
    RefPlot = False


class StrategyRef(BacktraderRef):
    pass


class StrategyRefDirective(BacktraderRefDirective):
    RefCls = Strategy
    RefPlot = False


class TALibIndRef(BacktraderRef):
    pass


class TALibIndRefDirective(BacktraderRefDirective):
    RefCls = _TALibIndicator
    RefPlot = True
    RefName = '_taindcol'


def setup(app):
    app.add_node(IndRef)
    app.add_directive('indref', IndRefDirective)

    app.add_node(DataBaseRef)
    app.add_directive('databaseref', DataBaseRefDirective)

    app.add_node(StrategyRef)
    app.add_directive('stratref', StrategyRefDirective)

    if TALibIndRefDirective.RefCls is not None:
        app.add_node(TALibIndRef)
        app.add_directive('talibindref', TALibIndRefDirective)

    return {'version': '0.2'}  # identifies the version of our extension

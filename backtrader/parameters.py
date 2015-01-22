#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
################################################################################
#
# Copyright (C) 2015 Daniel Rodriguez
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
################################################################################

class Parameter(object):
    def __init__(self, default):
        self.default = default
        # Allow access to descriptor __call__ via 'None' (ex: get default value)
        self.cache = dict([[None, self],])

    def __set__(self, obj, value):
        self.cache[obj] = value

    def __get__(self, obj, cls=None):
        return self.cache.setdefault(obj, self.default)

    def __call__(self):
        return self


class Params(object):
    _getparamsbase = classmethod(lambda cls: ())
    _getparams = classmethod(lambda cls: ())

    @classmethod
    def _derive(cls, name, params):
        # Prepare the full param list newclass = (baseclass + subclass)
        newparams = cls._getparams() + params

        # Create subclass
        newcls = type(cls.__name__ + '_' + name, (cls,), {})

        # Keep a copy of _getparams ... to access the params
        setattr(newcls, '_getparamsbase', getattr(newcls, '_getparams'))

        # Set the lambda classmethod in the new class that returns the new params (closure)
        setattr(newcls, '_getparams', classmethod(lambda cls: newparams))

        # Create Parameter descriptors for new params, the others come from the base class
        for pname, pdefault in params:
            setattr(newcls, pname, Parameter(pdefault))

        # Return the result
        return newcls

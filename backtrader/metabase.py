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

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import itertools
import sys


def findbases(kls, topclass):
    for base in kls.__bases__:
        if issubclass(base, topclass):
            lst = findbases(base, topclass)
            return lst.append(base) or lst

    return []


def findowner(owned, cls):
    # skip this frame and the caller's -> start at 2
    for framelevel in itertools.count(2):
        try:
            frame = sys._getframe(framelevel)
        except ValueError:
            # Frame depth exceeded ... no owner ... break away
            break

        # 'self' in regular code
        self_ = frame.f_locals.get('self', None)
        if self_ != owned and isinstance(self_, cls):
            return self_

        # '_obj' in metaclasses
        obj_ = frame.f_locals.get('_obj', None)
        if obj_ != owned and isinstance(obj_, cls):
            return obj_

    return None


class MetaBase(type):
    def doprenew(cls, *args, **kwargs):
        return cls, args, kwargs

    def donew(cls, *args, **kwargs):
        _obj = cls.__new__(cls, *args, **kwargs)
        return _obj, args, kwargs

    def dopreinit(cls, _obj, *args, **kwargs):
        return _obj, args, kwargs

    def doinit(cls, _obj, *args, **kwargs):
        _obj.__init__(*args, **kwargs)
        return _obj, args, kwargs

    def dopostinit(cls, _obj, *args, **kwargs):
        return _obj, args, kwargs

    def __call__(cls, *args, **kwargs):
        cls, args, kwargs = cls.doprenew(*args, **kwargs)
        _obj, args, kwargs = cls.donew(*args, **kwargs)
        _obj, args, kwargs = cls.dopreinit(_obj, *args, **kwargs)
        _obj, args, kwargs = cls.doinit(_obj, *args, **kwargs)
        _obj, args, kwargs = cls.dopostinit(_obj, *args, **kwargs)
        return _obj


class AutoInfoClass(object):
    _getpairsbase = classmethod(lambda cls: ())
    _getpairs = classmethod(lambda cls: ())
    _getrecurse = classmethod(lambda cls: False)

    @classmethod
    def _derive(cls, name, info, recurse=False):
        newinfo = collections.OrderedDict(cls._getpairs())

        info = collections.OrderedDict(info)
        newinfo.update(info)

        # str for Python 2/3 compatibility
        newcls = type(str(cls.__name__ + '_' + name), (cls,), {})

        setattr(newcls, '_getpairsbase', getattr(newcls, '_getpairs'))
        setattr(newcls, '_getpairs', classmethod(lambda cls: tuple(newinfo.items())))
        setattr(newcls, '_getrecurse', classmethod(lambda cls: recurse))

        for infoname, infoval in info.items():
            if recurse:
                recursecls = getattr(newcls, infoname, AutoInfoClass)
                infoval = recursecls._derive(name + '_' + infoname, infoval)

            setattr(newcls, infoname, infoval)

        return newcls

    def _get(self, name, default=None):
        return getattr(self, name, default)

    @classmethod
    def _getkwargsdefault(self):
        return collections.OrderedDict(cls._getpairs())

    def _getkwargs(self, skip_=False):
        l = [(x, getattr(self, x)) for x in self._getkeys() if not skip_ or not x.startswith('_')]
        return collections.OrderedDict(l)

    @classmethod
    def _getdefaults(cls):
        return [x[1] for x in cls._getpairs()]

    def _getvalues(self):
        return [getattr(self, x[0]) for x in self._getpairs()]

    @classmethod
    def _getkeys(cls):
        return [x[0] for x in cls._getpairs()]

    def __new__(cls, *args, **kwargs):
        obj = super(AutoInfoClass, cls).__new__(cls, *args, **kwargs)

        if cls._getrecurse():
            for infoname in obj._getkeys():
                recursecls = getattr(cls, infoname)
                setattr(obj, infoname, recursecls())

        return obj


class MetaParams(MetaBase):
    def __new__(meta, name, bases, dct):
        # Remove params from class definition to avod inheritance (and hence "repetition")
        newparams = dct.pop('params', ())

        # Create the new class - this pulls predefined "params"
        cls = super(MetaParams, meta).__new__(meta, name, bases, dct)

        # Pulls the param class out of it - default is the empty class
        params = getattr(cls, 'params', AutoInfoClass)

        # Subclass and store the newly derived params class
        cls.params = params._derive(name, newparams)

        return cls

    def donew(cls, *args, **kwargs):
        # Create params and set the values from the kwargs
        params = cls.params()
        for pname, pdef in cls.params._getpairs():
            setattr(params, pname, kwargs.pop(pname, pdef))

        # Create the object and set the params in place
        _obj, args, kwargs = super(MetaParams, cls).donew(*args, **kwargs)
        _obj.params = params
        _obj.p = params # shorter alias

        # Parameter values have now been set before __init__
        return _obj, args, kwargs

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
import abc
import itertools
import sys

# Subclassing from ABCMeta allows later the entire hierarchy to have abstract methods

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


class MetaBase(abc.ABCMeta):
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

    def _getkwargs(self):
        return dict(map(lambda x: (x[0], getattr(self, x[0])), self._getparams()))


class MetaParams(MetaBase):
    def __new__(meta, name, bases, dct):
        # Remove params from class definition to avod inheritance (and hence "repetition")
        newparams = dct.pop('params', ())

        # Create the new class - this pulls predefined "params"
        cls = super(MetaParams, meta).__new__(meta, name, bases, dct)

        # Pulls the param class out of it - default is the empty class
        params = getattr(cls, 'params', Params)

        # Subclass and store the newly derived params class
        cls.params = params._derive(name, newparams)

        return cls

    def dopreinit(cls, _obj, *args, **kwargs):
        _obj, args, kwargs = super(MetaParams, cls).dopreinit(_obj, *args, **kwargs)
        obj = cls.__new__(cls, *args, **kwargs)
        # Create params and set the values from the kwargs
        _obj.params = cls.params()
        for kname in kwargs.keys():
            if hasattr(_obj.params, kname):
                setattr(_obj.params, kname, kwargs.pop(kname))
        obj.params = cls.params()

        # Parameter values have now been set before __init__
        return _obj, args, kwargs

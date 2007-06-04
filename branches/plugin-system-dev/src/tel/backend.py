# -*- coding: utf-8 -*-
# base classes for backends
# Copyright (c) 2007 Sebastian Wiesner <basti.wiesner@gmx.net>

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


"""This module provides base classes and utility functions, which may be
used by backends"""


import itertools


__revision__ = '$Id$'


class Phonebook(object):
    """Base class for all phonebook classes defined by backends.

    Note, that although this class supports access by indexes, this is
    absolutely *not* recommended. Indexes may change when reloading
    phonebooks.

    Access to entries should happen using iterators or the find_all method.
    """
    def __init__(self, uri):
        self.uri = uri
        self.entries = []

    def load():
        """Loads entries from backend"""
        raise NotImplementedError()

    def save():
        """Loads entries from backend"""
        raise NotImplementedError()

    def __delitem__(self, index):
        del self._entries[index]

    def __getitem__(self, index):
        return self._entries[index]

    def __setitem__(self, key, entry):
        return self._entries[key] = entry

    def __contains__(self, entry):
        return entry in self._entries

    def __iter__(self):
        return iter(self._entries)

    def remove(self, entry):
        """Removes `entry`"""
        self._entries.remove(entry)          

    def add(self, entry):
        """Adds `entry`"""
        self._entries.append(entry)

    def sort_by_field(self, field, descending=False, ignore_case=False):
        """Returns a sorted list of entries in this phonebook"""
        def keyfunc(entry):
            value = entry[field]
            if isinstance(value, basestring) and ignore_case:
                return value.lower()
            return value
        return sorted(self, key=keyfunc, reverse=descending)

    def find_all(self, pattern, *fields):
        """Searchs this phonebook for certain patterns.
        `pattern` may either be

        - a plain string, which is searched in `fields`
        - a regular expression, which is matched against the content of
          `fields`
        - a callable object, which gets an entry object as parameter and
          may return a boolean value indicating, if the entry is matched.

        If the last form of invocation is used, *fields is ignored."""
        if callable(pattern):
            return [entry for entry in entries if pattern(entry)]
        # if fields are empty raise ValueError
        if not fields:
            raise ValueError(u'No fields specified')
        
        entries = []
        if isinstance(pattern, basestring):
            for entry in self:
                for field in fields:
                    if pattern in entry[field]:
                        entries.append(entry)
                        break
        else:
            # assume pattern is a regular expression
            for entry in self:
                for field in fields:
                    if pattern.match(entry[field]):
                        entries.append(entry)
                        break
        return entries
                        
            
            
        

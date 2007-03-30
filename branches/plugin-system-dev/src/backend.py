# -*- coding: utf-8 -*-
# module to manage phonebooks
# Copyright (c) 2007 Sebastian Wiesner
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the \"Software\"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""This module contains useful classes for backends

:mvar FIELDS: all fields supported by tel (same as in phonebook.FIELDS)"""


__revision__ = '$Id$'


import UserDict
import re
import itertools


import phonebook
from tel import config


_ = config.translation.ugettext


FIELDS = phonebook.FIELDS


class StandardEntry(phonebook.BaseEntry):
    """This class provides a standard entry class. Storage modules, which
    have no need to create special attributes, can rely on this class.

    :ivar fields: The dictionary storing all fields
    """
    def __init__(self):
        # init all fields
        self.fields = dict.fromkeys(FIELDS, empty)

    def _set(self, field, value):
        self.fields[field] = value

    def _get(self, field):
        return self.fields[field]    


class DictStorage(object):
    """This class provides a simple storage mixin, which uses a dictionary
    to map entries to their indicies.
    Additionally it supports auto-assigned indicies for new entries.
    Use this class, if you are writing your own backend. You just have to
    implement load and save methods, the rest is taken over by this class

    :ivar uri: The uri from which this Phonebook was loaded.
    :ivar entries: The dicitionary containing all entries
    """

    def __init__(self, uri):
        """Creates a PhoneBook from the file denoted by `path`"""
        self.uri = uri
        self.entries = {}

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise IndexError('Invalid index')
        return self.entries[key]

    def __repr__(self):
        return repr(self.entries)

    def __setitem__(self, key, entry):
        if key is None:
            # use the entry's key
            key = entry['index']
        if key is None:
            raise IndexError('None is no valid entry index')
        if isinstance(key, int):
            # make sure index and key are identical
            entry.index = key
            self.entries[key] = entry            
        elif isinstance(key, slice):
            # TODO support slice objects
            raise TypeError('No slice support')

    def __delitem__(self, key):
        if isinstance(key, int):
            del self.entries[key]
        elif isinstance(key, slice):
            # TODO support slice objects
            raise TypeError('No slice support')

    def __iter__(self):
        # iterate over the values of _entries here, since the key is present
        # in Entry.index
        return self.entries.itervalues()

    def __contains__(self, item):
        if isinstance(item, int):
            # regard item as an index
            return item in self.entries
##         elif isinstance(item, basestring):
##             return len(self.search(item)) > 0
        else:
            # regard item as an entry
            return item in self.entries.values()

    def append(self, entry):
        """Add the new `entry`.
        :raises ValueError: if entry['index'] is not None"""
        if entry['index'] is not None:
            raise ValueError('Entry has already an index')
        # generate a free index
        for i in itertools.count():
            if not self.entries.has_key(i):
                entry['index'] = i
                self[None] = entry
                break

##     def search(self, *args, **kwargs):
##         """Searchs the phone book.
##         `*args` and `**kwargs` are the same as for Entry.matches"""
##         found_entries = []
##         for entry in self:
##             if entry.matches(*args, **kwargs):
##                 found_entries.append(entry)
##         return found_entries

    def remove(self, entry):
        """Remove `entry`."""
        # make sure we remove the _same_ entry object
        if entry in self.entries.values():
            del self.entries[entry['index']]

    def create_new(self):
        """Returns a new entry. Note, that you have to add it manually"""
        raise NotImplementedError()

    def save(self):
        """Saves the phonebook"""
        raise NotImplementedError()

    def load(self):
        """Loads the phonebook"""
        raise NotImplementedError()

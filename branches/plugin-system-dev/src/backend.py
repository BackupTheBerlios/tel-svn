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


def prettify(entry):
    """Returns a nice string representation of `entry`"""
    # return a pretty representation
    # NOTE: this doesn't respect field translations to allow pretty
    # printing without being bound to field limits
    # TODO: use textwrap here to prevent overlong lines    
    msg = _('Index:          %(index)s\n'
            'Name:           %(firstname)s %(lastname)s\n'
            'Street:         %(street)s\n'
            'Town:           %(postcode)s %(town)s\n'
            'Phone:          %(phone)s\n'
            'Mobile:         %(mobile)s\n'
            'eMail:          %(email)s\n'
            'Date of birth:  %(birthdate)s\n'
            'Tags:           %(tags)s\n') % entry
    return msg


class StandardEntry(UserDict.DictMixin):
    """This class provides a standard entry class. Storage modules, which
    have no need to create special attributes, can rely on this class.
    Each field can be assigned to a checking method, which verifies the
    correctness of the field. This methods are assigned int the CHECKERS
    dict.

    The following attributes are supported:
    fields, which holds a dictionary of all fields except for index,
    index, which stores the index.
    The index is available only through the readonly index property.

    Custom entry classes must emulate the behaviour of this class.
    In particular, the need to support a mapping interface to the fields.
    Additionally the need to provide a not_indexed method, which returns
    True, if the entry has not been assigned with an index.
    Entries must support string formatting through str and unicode.
    """

    # a simple pattern for phone numbers
    PHONE_NUMBER_PATTERN = re.compile(r'^[-()/\d\s\W]+$')
    # a simple pattern for mail addresses
    MAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[\w]+$')

    def _check_unicode(self, value):
        return unicode(value)
        
    def _check_int(self, value):
        return int(value)

    def _check_phone(self, value):
        if self.PHONE_NUMBER_PATTERN.match(value):
            return self._check_unicode(value)
        else:
            raise ValueError('Invalid literal for phone number: %s'
                             % value)

    def _check_email(self, value):
        if self.MAIL_PATTERN.match(value):
            return self._check_unicode(value)
        else:
            raise ValueError('Invalid literal for email address: %s'
                             % value)

    def _check_numeric(self, value):
        """Checks if value is a number, but returns it as string"""
        int(value)
        return value

    # dictionary for type checking methods
    CHECKERS = {
        'index': _check_int,
        'firstname': _check_unicode,
        'lastname': _check_unicode,
        'street': _check_unicode,
        'postcode': _check_numeric,
        'town': _check_unicode,
        'mobile': _check_phone,
        'phone': _check_phone,
        'email': _check_email,
        # FIXME: use egenix datetime here to verify dates
        'birthdate': _check_unicode,
        'tags': _check_unicode
        }

    def __init__(self):
        # init all fields
        self.fields = dict.fromkeys(FIELDS, u'')
        self.fields['index'] = None

    # dict interface
    def keys(self):
        """Return a list of all keys, which is basically a copy of
        `FIELDS`"""
        return list(FIELDS)

    def __getitem__(self, key):      
        if key not in FIELDS:
            raise KeyError('Invalid field %s' % key)
        return self.fields[key]

    def __setitem__(self, key, value):
        if key not in FIELDS:
            raise KeyError('Invalid field %s' % key)
        # check non-empty values
        if value:
            value = self.CHECKERS[key](self, value)
        self.fields[key] = value

    def __delitem__(self, key):
        if key not in FIELDS:
            raise KeyError('Invalid field %s' % key)
        del self.fields[key]

    def __str__(self):
        return prettify(self)

    def __nonzero__(self):
        for field in FIELDS[1:]:
            # ignore index, since empty entries can have indicies, too
            if self.fields[field]:
                return True
        return False

    def __repr__(self):
        # return a short representation
        return repr(self.fields)

    def not_indexed(self):
        """Returns True, if this entry is not indexed"""
        return (self['index'] is None)


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
        return iter(self.entries.values())

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

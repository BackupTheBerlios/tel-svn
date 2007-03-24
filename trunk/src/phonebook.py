#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
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

"""This module provides classes to manage a phone book.

:mvar FIELDS: all fields supported by tel's phonebooks"""


__revision__ = '$Id$'
__all__ = ['FIELDS', 'PhoneBook', 'Entry', 'sort_entries_by_field',
           'translate_field']


import os
import re
import csv
import itertools
import gettext

import tel

_ = gettext.translation('tel', tel.CONFIG.MESSAGES).ugettext


# mainly important for table printing and field specifications
_TRANSLATIONS = {
    'index': _('Index'),
    'firstname': _('First name'),
    'lastname': _('Last name'),
    'street': _('Street and number'),
    'postcode': _('Postal code'),
    'town': _('Town'),
    'mobile': _('Mobile'),
    'phone': _('Phone'),
    'email': _('eMail'),
    'birthdate': _('Date of birth'),
    'tags': _('Tags')
}


FIELDS = ('index', 'firstname', 'lastname', 'street', 'postcode',
          'town', 'mobile', 'phone', 'email', 'birthdate', 'tags')


class Entry(object):
    """This class stores a single adress entry.
    
    :ivar index: a unique index (like a db primary key)
    :ivar firstname:
    :ivar lastname:
    :ivar street:
    :ivar postcode:
    :ivar town:
    :ivar mobile:
    :ivar phone:
    :ivar email:
    :ivar birthdate:
    :ivar tags: The famous web 2.0 thingy
    """

    # FIXME: convert attributes into properties to support type checking
    # FIXME: we could use new style classes here
                  
    def __init__(self):
        # init all fields
        self.index = None
        self.firstname = ''
        self.lastname = ''
        self.street = ''
        self.postcode = ''
        self.town = ''
        self.mobile = ''
        self.phone = ''
        self.email = ''
        self.birthdate = ''
        self.tags = ''

    def __str__(self):
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
                'Tags:           %(tags)s\n') % self.__dict__
        return msg

    def __lt__(self, other):
        return NotImplemented

    def __le__(self, other):
        return NotImplemented

    def __gt__(self, other):
        return NotImplemented

    def __ge__(self, other):
        return NotImplemented

    def __ne__(self, other):
        for field in FIELDS:
            if getattr(self, field) != getattr(other, field):
                return True
        return False

    def __eq__(self, other):
        return not self.__ne__(other)

    def __hash__(self):
        hash_ = 0
        for field in FIELDS:
            hash_ ^= hash(getattr(self, field))
        return hash_

    def __repr__(self):
        # return a short representation
        msg = _('[%(index)s] %(firstname)s %(lastname)s') % self.__dict__
        return msg

    def __nonzero__(self):
        # whether the entry is empty. an empty entry is an entry whose
        # fields (except index) are empty.  Since index is auto-created on
        # most cases, an empty entry can have an index.
        for field in FIELDS:
            if field != 'index' and getattr(self, field):
                return True
        return False

    def matches(self, pattern, ignore_case=False, regexp=False,
                fields=None):
        """Note, that this method does *not* support regular expressions.
        :param pattern: A string pattern, which is searched in this entry
        :param regexp: Whether pattern is a regular expression or not
        :param fields: the fields to search in
        :returns: True, if any field in this entry matches `pattern`,
        False otherwise"""
        if fields is None:
            fields = FIELDS
        for field in fields:
            if regexp:
                flags = re.UNICODE | re.LOCALE
                if ignore_case:
                    flags = flags | re.IGNORECASE
                if bool(re.search(pattern, str(getattr(self, field)),
                                  flags)):
                    return True
            else:
                value = str(getattr(self, field))
                if ignore_case:
                    pattern = pattern.lower()
                    value = value.lower()
                # very simple searching algo ;)
                if pattern in value:
                    return True
        return False


class PhoneBook:
    """This class provides an interface to the phone book

    :ivar path: The file, from which this Phonebook was loaded.
    """

    def __init__(self, path):
        """Creates a PhoneBook from the file denoted by `path`"""
        self._entries = None
        self.path = path
        self.load()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._entries[key]
        elif isinstance(key, slice):
            raise NotImplementedError('__setitem__ not implemented for '
                                      'slices')
            # TODO support slice objects

    def __setitem__(self, key, value):
        if not isinstance(value, Entry):
            raise TypeError('PhoneBook only supports Entry objects')
        if not key:
            if value.index is not None:
                # use the index of entry
                key = value.index
            else:
                # search a free index
                for i in itertools.count():
                    if i not in self._entries.keys():
                        key = i
                        break
        if isinstance(key, int):
            # make sure index and key are identical
            value.index = key
            self._entries[key] = value
        elif isinstance(key, slice):
            # TODO support slice objects
            raise NotImplementedError('__getitem__ not implemented for '
                                      'slices')

    def __delitem__(self, key):
        if isinstance(key, int):
            del self._entries[key]
        elif isinstance(key, slice):
            # TODO support slice objects
            raise NotImplementedError('__delitem__ not implemented for '
                                      'slices')

    def __iter__(self):
        # iterate over the values of _entries here, since the key is present
        # in Entry.index
        return iter(self._entries.values())

    def __contains__(self, item):
        if isinstance(item, int):
            # regard item as an index
            return item in self._entries
        elif isinstance(item, Entry):
            # regard item as an entry
            return item in self._entries.values()
        elif isinstance(item, basestring):
            return len(self.search(item)) > 0

    def load(self):
        """Loads the phone book from the file.
        **WARNING:** This resets the `entries` list. All changes made after
        the last invocation of _`save()` will be lost"""
        self._entries = {}
        if os.path.exists(self.path):
            reader = csv.DictReader(open(self.path, 'rb',))
            for row in reader:
                entry = Entry()
                for k in row:
                    setattr(entry, k, row[k].decode('utf-8'))
                # make sure we have an integer as key
                entry.index = int(entry.index)
                self._entries[entry.index] = entry

    def save(self):
        """Writes the phone book back to the file"""
        stream = open(self.path, 'wb',)
        # write a head line containing the names of the fields
        writer = csv.writer(stream)
        writer.writerow(FIELDS)
        # write all entries
        writer = csv.DictWriter(stream, FIELDS, extrasaction='ignore')
        for entry in self._entries.values():
            for field in FIELDS:
                value = unicode(getattr(entry, field))
                setattr(entry, field, value.encode('utf-8'))
            writer.writerow(entry.__dict__)
        stream.close()

    def add(self, entry):
        """Adds `entry` to the phone book. If the _index property of `entry`
        is None, then the index is autogenerated. If it already has a value,
        this value is used as index. Any entry, which has this index, is
        overwritten. You can use this behaviour to replace entries in the
        phone book"""
        self[entry.index] = entry

    def remove(self, entry):
        """Remove `entry`. If `entry` is an integer, it is assumed to be the
        index of the entry to remove. If `entry` is an instance of Entry,
        the property index is used as the index"""
        index = None
        if isinstance(entry, Entry):
            index = entry.index
        elif isinstance(entry, int):
            index = entry
        del self[index]

    def search(self, *args, **kwargs):
        """Searchs the phone book.
        `*args` and `**kwargs` are the same as for Entry.matches"""
        found_entries = []
        for entry in self:
            if entry.matches(*args, **kwargs):
                found_entries.append(entry)
        return found_entries

    def decrypt(self):
        """Decrypts phonebook"""
        # TODO implement
        raise NotImplementedError('Encryption is not yet supported')

    def encrypt(self):
        """Encrypts phonebook"""
        # TODO implement
        raise NotImplementedError('Encryption is not yet supported')


def sort_entries_by_field(iterable, field, descending):
    """This sorts `iterable`, which may only contain Entry objects, by
    `field`, which may be be any of Entry.default_order. If `descending is
    True, the list is reversed."""
    def key_func(entry):
        return getattr(entry, field)
    return sorted(iterable, key=key_func, reverse=descending)


def translate_field(field):
    """:returns: A translation for `field`
    :raises ValueError: If `field` is not in _FIELDS"""
    try:
        return _TRANSLATIONS[field]
    except KeyError:
        raise ValueError(_('There is no field %s') % field)
        

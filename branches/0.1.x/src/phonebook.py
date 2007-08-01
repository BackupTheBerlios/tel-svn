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
import UserDict

import tel


_ = tel.CONFIG.TRANSLATION.ugettext


# mainly important for table printing and field specifications
_TRANSLATIONS = {
    'index': _('Index'),
    'title': _('Title'),
    'firstname': _('First name'),
    'lastname': _('Last name'),
    'street': _('Street and number'),
    'postcode': _('Postal code'),
    'town': _('Town'),
    'country': _('Country'),
    'postbox': _('Post office box'),
    'mobile': _('Mobile'),
    'phone': _('Phone'),
    'email': _('eMail'),
    'birthdate': _('Date of birth'),
    'tags': _('Tags')
}


FIELDS = ('index', 'title', 'firstname', 'lastname', 'street', 'postcode',
          'town', 'country', 'postbox', 'mobile', 'phone', 'email',
          'birthdate', 'tags')


class Entry(UserDict.DictMixin):
    """This class stores a single adress entry.
    It supports a dictionary interface for setting field values.
    Supported fields are listed in `FIELDS`."""

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

    # dictionary for type checking methods
    CHECKERS = {
        'index': _check_int,
        'title': _check_unicode,
        'firstname': _check_unicode,
        'lastname': _check_unicode,
        'street': _check_unicode,
        'postcode': _check_unicode,
        'town': _check_unicode,
        'country': _check_unicode,
        'postbox': _check_int,
        'mobile': _check_phone,
        'phone': _check_phone,
        'email': _check_email,
        # FIXME: use egenix datetime here to verify dates
        'birthdate': _check_unicode,
        'tags': _check_unicode
        }

    def __init__(self):
        # init all fields
        self.__dict__ = dict.fromkeys(FIELDS, u'')
        self.index = None

    # dict interface

    def keys(self):
        """Return a list of all keys, which is basically a copy of
        `FIELDS`"""
        return list(FIELDS)

    def __getitem__(self, key):
        if key not in FIELDS:
            raise KeyError('Invalid field %s' % key)
        return getattr(self, key)

    def __setitem__(self, key, value):
        if key not in FIELDS:
            raise KeyError('Invalid field %s' % key)
        setattr(self, key, value)

    def __delitem__(self, key):
        if key not in FIELDS:
            raise KeyError('Invalid field %s' % key)
        delattr(self, key)

    # rest of mapping methods defined by DictMixin

    def __setattr__(self, name, value):
        if name in FIELDS:
            if value:
                # only check non-empty fields
                value = self.CHECKERS[name](self, value)
            self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def __delattr__(self, name):
        if name in FIELDS:
            if name == 'index':
                self.__dict__[name] = None
            else:
                self.__dict__[name] = u''
        else:
            del self.__dict__[name]

    def __str__(self):
        # return a pretty representation
        # NOTE: this doesn't respect field translations to allow pretty
        # printing without being bound to field limits
        # TODO: use textwrap here to prevent overlong lines
        msg = _('Index:           %(index)s\n'
                'Title:           %(title)s\n'
                'Name:            %(firstname)s %(lastname)s\n'
                'Street:          %(street)s\n'
                'Address:         %(country)s, %(postcode)s %(town)s\n'
                'Post office box: %(postbox)s\n'
                'Phone:           %(phone)s\n'
                'Mobile:          %(mobile)s\n'
                'eMail:           %(email)s\n'
                'Date of birth:   %(birthdate)s\n'
                'Tags:            %(tags)s\n') % self
        return msg

    # nonzero is missing
    def __nonzero__(self):
        for field in FIELDS[1:]:
            # ignore index, since empty entries can have indicies, too
            if self[field]:
                return True
        return False

    def __repr__(self):
        # return a short representation
        fields = {}
        for field in FIELDS:
            fields[field] = self.__dict__[field]
        return repr(fields)

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
                    if bool(re.search(pattern, unicode(self[field]),
                                      flags)):
                        return True
            else:
                value = unicode(self[field])
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
                    entry[k] = row[k].decode('utf-8')
                self._entries[entry.index] = entry

    def save(self):
        """Writes the phone book back to the file"""
        stream = open(self.path, 'wb',)
        # write a head line containing the names of the fields
        writer = csv.writer(stream)
        writer.writerow(FIELDS)
        for entry in self._entries.values():
            row = []
            for field in FIELDS:
                value = unicode(entry[field]).encode('utf-8')
                row.append(value)
            writer.writerow(row)
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


def sort_entries_by_field(entries, field, descending=False,
                          ignore_case=False):
    """This sorts `iterable`, which may only contain Entry objects, by
    `field`, which may be be any of Entry.default_order. If `descending is
    True, the list is reversed. If `ignore_case` is True, case is ignored
    when sorting"""
    def keyfunc(entry):
        value = entry[field]
        if isinstance(value, basestring) and ignore_case:
            return value.lower()
        return value

    return sorted(entries, key=keyfunc, reverse=descending)


def translate_field(field):
    """:returns: A translation for `field`
    :raises ValueError: If `field` is not in _TRANSLATIONS"""
    try:
        return _TRANSLATIONS[field]
    except KeyError:
        raise ValueError('There is no field %s' % field)

# -*- coding: utf-8 -*-
# module to manage phonebooks
# Copyright (c) 2007 Sebastian Wiesner
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


"""This module provides classes to manage a phone book."""


__revision__ = '$Id$'


import re
import UserDict

from tel import teltypes
from tel import backendmanager
from tel import config


_ = config.translation.ugettext


FIELDS = ('title', 'firstname', 'lastname', 'street', 'postcode',
          'town', 'country', 'postbox', 'mobile', 'phone', 'email',
          'birthdate', 'tags')


# this contains a mapping of field names to valuable information about
# fields. The first tuple item contains the preferred translation for a
# field, the second the type of the field
# NOTE: You should never use this mapping directly. Instead use the
# functions provided by this module
_FIELD_INFORMATION = {
    'title': (_(u'Title'), unicode),
    'firstname': (_(u'First name'), unicode),
    'lastname': (_(u'Last name'), unicode),
    'street': (_(u'Street and number'), unicode),
    'postcode': (_(u'Postal code'), unicode),
    'town': (_(u'Town'), unicode),
    'country': (_(u'Country'), unicode),
    'postbox': (_(u'Post office box'), int),
    'mobile': (_(u'Mobile'), teltypes.phone_number),
    'phone': (_(u'Phone'), teltypes.phone_number),
    'email': (_(u'eMail'), teltypes.email),
    'birthdate': (_(u'Date of birth'), unicode),
    'tags': (_(u'Tags'), unicode)
}


class NoSuchField(Exception):
    """Raised on access to invalid fields"""
    def __init__(self, field):
        self.field = field
        Exception.__init__(self, _('No such field: %s') % field)


class Phonebook(object):
    """Base class for all phonebook classes defined by backends.

    Note, that although this class supports access by indexes, this is
    absolutely *not* recommended. Indexes may change when reloading
    phonebooks.

    Access to entries should happen using iterators or the find_all method.
    """

    # defaults to FIELDS
    # overwrite to change the list of supported fields
    fields = None

    def __init__(self, uri):
        self.uri = uri
        self._entries = []

    def load(self):
        """Loads entries from backend"""
        raise NotImplementedError()

    def save(self):
        """Loads entries from backend"""
        raise NotImplementedError()

    def __delitem__(self, index):
        if isinstance(index, slice):
            for entry in self._entries[index]:
                entry.parent = None
        else:
            self._entries[index].parent = None
        del self._entries[index]

    def __getitem__(self, index):
        return self._entries[index]

    def __setitem__(self, index, entry):
        if isinstance(index, slice):
            for e in entry:
                e.parent = self
        else:
            entry.parent = self
        self._entries[index] = entry

    def __contains__(self, entry):
        return entry in self._entries

    def __iter__(self):
        return iter(self._entries)

    def clear(self):
        """Removes all entries"""
        self._entries = []

    def remove(self, entry):
        """Removes `entry`"""
        self._entries.remove(entry)
        entry.parent = None

    def add(self, entry):
        """Adds `entry`"""
        if entry.parent is not None:
            # copy entry, if it is already contained in a phonebook
            entry = Entry(entry)
        entry.parent = self
        self._entries.append(entry)

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
            return [entry for entry in self if pattern(entry)]
        # if fields are empty raise ValueError
        if not fields:
            raise ValueError(u'No fields specified')

        entries = []
        if isinstance(pattern, basestring):
            # plain text comparison
            for entry in self:
                if any((unicode(entry[f]) == pattern for f in fields)):
                    entries.append(entry)
        else:
            # regular expression search
            for entry in self:
                if any((pattern.search(unicode(entry[f])) for f in fields)):
                    entries.append(entry)
        return entries

    @classmethod
    def supported_fields(cls):
        """Returns a list of all supported fields

        Basically it just inteprets the fields attribute.
        If this attribute is None, then it returns FIELDS.

        This is a classmethod, as this information is shared
        across all instances of this class."""
        return cls.fields or FIELDS


class Entry(object, UserDict.DictMixin):
    """This class represents a single entry in a phonebook.
    It supports all fields present in the FIELDS tuple.

    :ivar parent: The phonebook, which contains this entry, or None, if this
    entry has not been added to a phonebook"""

    def __init__(self, entry=None, **kwargs):
        """If `entry` is given, copy all fields from `entry`.
        Any keyword arguments are regarded as field values, and are stored
        if no other value has been given"""
        self.parent = None
        self.fields = dict.fromkeys(FIELDS, "")
        if entry:
            # copy constructor
            self.fields.update(entry)
        for k in kwargs:
            self.setdefault(k, kwargs[k])

    def keys(self):
        """Return a list of all keys, which is basically a copy of
        `FIELDS`"""
        return list(FIELDS)

    def __getitem__(self, field):
        if field not in FIELDS:
            raise NoSuchField(field)
        return self.fields[field]

    def __unicode__(self):
        return config.short_entry_format % self

    __str__ = __unicode__

    def __repr__(self):
        return '%s "%s %s" at %s' % (self.__class__.__name__,
                                     self['firstname'], self['lastname'],
                                     id(self))

    def prettify(self):
        """Returns a pretty representation of this entry"""
        return config.long_entry_format % self

    def __setitem__(self, field, value):
        if field not in FIELDS:
            raise KeyError(u'Invalid field %s' % field)
        # get the field type
        ftype = field_type(field)
        if value != '' and not isinstance(value, ftype):
            # convert the given value into the field type
            value = ftype(value)
        self.fields[field] = value

    def __delitem__(self, field):
        if field not in FIELDS:
            raise KeyError(u'Invalid field %s' % field)
        self.fields[field] = ''

    def __nonzero__(self):
        return any((self[field] != '' for field in self))

    def setdefault(self, field, default=None):
        """Sets field to `value`, if field is empty"""
        if self[field] == '':
            self[field] = default
        return self[field]

    def __contains__(self, field):
        """Returns True, if `field` contains a non-empty value"""
        return self[field] != ''

    def __iter__(self):
        return iter(FIELDS)

    def iteritems(self):
        """Returns an iterator over key, value pairs"""
        return ((field, self[field]) for field in self)


class URI(object):
    """Encapsulates a phonebook uri.

    An uri is separated in the scheme and the location part.
    The scheme is the name of the backend, which shall be used to load
    location. Both parts a separated by the usual url separator ://.
    See uri_pattern for the regular expression which is used to extract
    the parts from an uri string."""

    # regular expression to extract single parts from an uri
    uri_pattern = re.compile(r'((?P<scheme>\w*)://)?(?P<location>.*)',
                             re.DOTALL | re.UNICODE)

    def __init__(self, *args):
        """Accepts one or two arguments. If there is only one argument,
        it is parsed according to `uri_pattern`, if there are two arguments,
        the first one is the scheme, the second the location"""
        # make sure module is initialized, so that we have a backendmanager
        # available
        self.scheme = None
        self.location = None

        if len(args) == 1:
            match = self.uri_pattern.match(args[0])
            if not match:
                raise ValueError(_(u'%s is not a valid URI.'))
            self.__dict__.update(match.groupdict())
        elif len(args) == 2:
            self.scheme, self.location = args

    def absuri(self):
        """Returns a new URI object containing the absolute uri
        (with a scheme)"""
        uri = URI(self.location)
        uri.absolutize()
        return (uri if uri.scheme else None)

    def absolutize(self):
        """Set the scheme of this URI by guessing it from location.
        Only changes scheme, if it is None or empty."""
        if not self.isabsolute():
            manager = backendmanager.manager()
            backend = manager.backend_for_file(self.location)
            if backend:
                self.scheme = backend.__name__

    def isabsolute(self):
        """Checks whether this URI is absolute"""
        return self.scheme is not None

    def __str__(self):
        if self.scheme:
            return self.scheme + '://' + self.location
        else:
            return self.location


def phonebook_open(uri):
    """Opens a phonebook denoted by `uri`. `uri` may be a plain string, or
    an instance of URI class.

    Note, that the returned phonebook instance doesn't contain entries.
    These must be loaded explicitly using the load() method"""
    if isinstance(uri, basestring):
        uri = URI(uri)
    # guess backend, if uri was not absolute (= no scheme was given)
    uri.absolutize()
    if uri.scheme is None:
        raise IOError(_(u'Couldn\'t find a backend for %s.') % uri)
    try:
        backend = backendmanager.manager()[uri.scheme]
    except KeyError:
        raise IOError(_(u'Unknown backend %s.') % uri.scheme)
    return backend.__phonebook_class__(uri)


# shortcut to sort entry iterables by a certain field
# it's just an easy wrapper around the sorted builtin, no big thing
def sort_by_field(entries, field, descending=False, ignore_case=False):
    """Returns a sorted list of entries in this phonebook"""
    def field_getter(entry):
        value = unicode(entry[field])
        return value.lower() if ignore_case else value
    return sorted(entries, key=field_getter, reverse=descending)


# functions to query field information
def translate_field(field):
    """:returns: A translation for `field`
    :raises ValueError: If `field` is not known"""
    try:
        return _FIELD_INFORMATION[field][0]
    except KeyError:
        raise NoSuchField(field)


def field_type(field):
    """Returns the type of `field`
    :raises ValueError: If `field` is not known"""
    try:
        return _FIELD_INFORMATION[field][1]
    except KeyError:
        raise NoSuchField(field)

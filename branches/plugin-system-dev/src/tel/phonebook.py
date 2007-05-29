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


import re
import UserDict

import teltypes
import backendmanager
from tel import config


_ = config.translation.ugettext


FIELDS = ('index', 'title', 'firstname', 'lastname', 'street', 'postcode',
          'town', 'country', 'postbox', 'mobile', 'phone', 'email',
          'birthdate', 'tags')


# this contains a mapping of field names to valuable information about
# fields. The first tuple item contains the preferred translation for a
# field, the second the type of the field
# NOTE: You should never use this mapping directly. Instead use the
# functions provided by this module
_field_information = {
    'index': (_('Index'), int),
    'title': (_('Title'), unicode),
    'firstname': (_('First name'), unicode),
    'lastname': (_('Last name'), unicode),
    'street': (_('Street and number'), unicode),
    'postcode': (_('Postal code'), unicode),
    'town': (_('Town'), unicode),
    'country': (_('Country'), unicode),
    'postbox': (_('Post office box'), int),
    'mobile': (_('Mobile'), teltypes.phone_number),
    'phone': (_('Phone'), teltypes.phone_number),
    'email': (_('eMail'), teltypes.email),
    'birthdate': (_('Date of birth'), unicode),
    'tags': (_('Tags'), unicode)
}


class Entry(object, UserDict.DictMixin):
    """This class represents a single entry in a phonebook.
    It supports all fields present in the FIELDS tuple."""
          
    def __init__(self, entry=None, **kwargs):
        """If `entry` is given, copy all fields from `entry`.
        Any keyword arguments are regarded as field values, and are stored
        if no other value has been given"""
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
            raise KeyError('Invalid field %s' % field)
        return self.fields[field]

    def __setitem__(self, field, value):
        if field not in FIELDS:
            raise KeyError('Invalid field %s' % field)
        # get the field type
        ftype = field_type(field)
        if value != '' and not isinstance(value, ftype):
            # convert the given value into the field type
            value = ftype(value)
        self.fields[field] = value

    def __delitem__(self, field):
        if field not in FIELDS:
            raise KeyError('Invalid field %s' % field)
        self.fields[field] = ''

    def __nonzero__(self):
        # ignore index, since empty entries can have indices too
        for field in FIELDS[1:]:
            if self[field] != '':
                return True
        return False

    def setdefault(self, field, value):
        """Sets field to `value`, if field is empty"""
        if self[field] == '':
            self[field] = value
        return self[field]

    def __contains__(self, field):
        """Returns True, if `field` contains a non-empty value"""
        return self[field] != ''

    def __iter__(self):
        return iter(FIELDS)

    def iteritems(self):
        """Returns an iterator over key, value pairs"""
        for field in self:
            yield (field, self[field])

    def has_index(self):
        """Returns True, if this entry is not indexed"""
        return (self['index'] != '')



class BaseStorage(object):
    # XXX: there seems to be no need for this!
    """The base class of all storage implementations.
    It's use is mainly for type testing and as a reference"""

    def __init__(self, uri):
        """Creates a new instance, which is bound to `uri`.
        load() and save() must operate on this `uri`"""
        raise NotImplementedError

    def __getitem__(self, indices):
        """Returns entries at the specified indices.
        Must support slice objects (NOT YET IMPLEMENTED)"""
        raise NotImplementedError

    def __delitem__(self, indices):
        """Remove the entries at the specified indices
        Must support slice objects (NOT YET IMPLEMENTED)."""
        raise NotImplementedError

    def __iter__(self):
        """Iterate over all entries in this storage"""
        raise NotImplementedError

    def __contains__(self, entry):
        """Check, whether `entry` is contained in this storage"""
        raise NotImplementedError

    def remove(self, entry):
        """Remove `entry`."""
        if entry in self:
            del self[entry['index']]

##     def search(self, *args, **kwargs):
##         """Searchs the phone book.
##         `*args` and `**kwargs` are the same as for Entry.matches"""
##         found_entries = []
##         for entry in self:
##             if entry.matches(*args, **kwargs):
##                 found_entries.append(entry)
##         return found_entries

    def append(self, entry):
        """Adds `entry` to this storage"""
        raise NotImplementedError()

    def save(self):
        """Saves the phonebook"""
        raise NotImplementedError()

    def load(self):
        """Loads entries into this storage"""
        raise NotImplementedError()
    


class URI(object):  
    """Encapsulates a phonebook uri.

    An uri is separated in the scheme and the location part.
    The scheme is the name of the backend, which shall be used to load
    location. Both parts a separated by the usual url separator ://.
    See uri_pattern for the regular expression which is used to extract
    the parts from an uri string."""
    # regular expression to extract single parts from an uri
    uri_pattern = re.compile(r'((?P<scheme>\w*)://)?(?P<location>.*)',
                             re.DOTALL)
    
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
                raise ValueError(_('%s is no valid URI'))
            self.__dict__.update(match.groupdict())
        elif len(args) == 2:
            self.scheme, self.location = args

    def absuri(self):
        """Returns a new URI object containing the absolute uri
        (with a scheme)"""
        uri = URI(self.location)
        uri.absolutize()
        return uri if uri.scheme else None

    def absolutize(self):
        """Set the scheme of this URI by guessing it from location.
        Only changes scheme, if it is None or empty."""
        if not self.isabsolute():
            manager = backendmanager.manager()
            backend = manager.backend_for_file(self.location)
            if backend:
                self.scheme = backend.name

    def isabsolute(self):
        """Checks whether this URI is absolute"""
        return self.scheme is not None

    def __str__(self):
        if self.scheme:
            return self.scheme + '://' + self.location
        else:
            return self.location



def phonebook_open(uri):
    """Open a phonebook from `uri`"""
    if isinstance(uri, basestring):
        uri = URI(uri)
    uri.absolutize()
    if uri.scheme is None:
        raise IOError(_('Couldn\'t determine backend for %s') % uri)
    try:
        backend = backendmanager.manager()[uri.scheme]
    except KeyError:
        raise IOError(_('No backend found for %s') % uri.scheme)
    storage = backend.storage_class
    return storage(uri.location)


# functions to query field information

def translate_field(field):  
    """:returns: A translation for `field`
    :raises ValueError: If `field` is not known"""
    try:
        return _field_information[field][0]
    except KeyError:
        raise ValueError('There is no field %s' % field)


def field_type(field):
    """Returns the type of `field`
    :raises ValueError: If `field` is not known"""
    try:
        return _field_information[field][1]
    except KeyError:
        raise ValueError('There is no field %s' % field)


# Utility functions
def long_prettify(entry):
    """Returns a pretty string representation of `entry`
    Note, that index is most likly excluded of this representation, since
    it should be usable for printing and can be changed by the user
    through a config file (not yet)"""
    # return a pretty representation
    # TODO: use textwrap here to prevent overlong lines
    return config.long_entry_format % entry


def short_prettify(entry):
    """Returns a short representation of `entry` suitable for printing it in
    lists."""
    return config.short_entry_format % entry


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

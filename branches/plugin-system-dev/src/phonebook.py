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


import os
import re

from tel import config
from backendmanager import BackendManager


_ = config.translation.ugettext


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


FIELDS = ('index', 'firstname', 'lastname', 'street', 'postcode', 'town',
          'mobile', 'phone', 'email', 'birthdate', 'tags')


# backend manager
_manager = None

def get_backendmanager():
    """Return the backend manager used by this module"""
    return _manager

def set_backendmanager(manager):
    """Set the backend manager used by this module"""
    global _manager
    _manager = manager

def initialized():
    """True, if this module is initialized"""
    return _manager is not None

def init(manager=None):
    """Intializes this module explicitly."""
    global _manager
    if not initialized():
        _manager = BackendManager()
        

class URI(object):
    """Encapsulates a phonebook uri"""
    # regular expression to extract single parts from an uri
    uri_pattern = re.compile(r'((?P<scheme>\w*)://)?(?P<location>.*)',
                             re.DOTALL)
    
    def __init__(self, *args):
        """Accepts one or two arguments. If there is only one argument,
        it is parsed according to `uri_pattern`, if there are two arguments,
        the first one is the scheme, the second the location"""
        # make sure module is initialized
        init()
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
        """Return the absolute uri (with a scheme)"""
        scheme = self.scheme
        if not scheme:
            # FIXME: implement auto-detection of uri
            manager = get_backendmanager()
            scheme = manager.find_backend_for_file(self.location).name
        return scheme + '://' + location

    def absolutize(self):
        """Set the scheme of this URI by guessing it from location.
        Only changes scheme, if it is None or empty."""
        if not self.isabsolute():
            manager = get_backendmanager()
            self.scheme = manager.find_backend_for_file(self.location).name

    def isabsolute(self):
        """Checks whether this URI is absolute"""
        return self.scheme is not None

    def __str__(self):
        if self.scheme:
            return self.scheme + '://' + self.location
        else:
            return self.location


def get_backend_for_uri(uri):
    """Tries to find a backend suitable for uri"""
    if uri.scheme is None:
        raise IOError(_('Couldn\'t determine backend for %s') % uri)

    try:
        return get_backendmanager().get_backend(uri.scheme)
    except KeyError:
        raise IOError(_('No backend found for %s') % uri.scheme)

        
def phonebook_open(uri):
    """Open a phonebook from `uri`"""
    if isinstance(uri, basestring):
        uri = URI(uri)
    uri.absolutize()

    backend = get_backend_for_uri(uri)
    storage = backend.storage_class
    return storage(uri.location)


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
        

# -*- coding: utf-8 -*-
# module to manage phonebook storage backends
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


"""This module provides access to phonebook backends."""


__revision__ = '$Id$'


import os
import imp

from UserDict import DictMixin

from tel import config


_ = config.translation.ugettext


MODULE_SUFFIXES = zip(*imp.get_suffixes())[0]
# this is the pattern used to expand a backend name
BACKEND_MODULE_PATTERN = u'%s_backend'


def get_backend_name(filename):
    """Returns the backend name for filename, or None, if filename is not a
    python module or no valid backend.

    The backend name is the module name, stripped of the python module
    suffix as returned by imp.get_suffixes and the suffix '_backend'

    *Note*: Iterators returned by this module silently ignore invalid
    backends"""
    for suffix in MODULE_SUFFIXES:
        suffix = '_backend' + suffix
        if filename.endswith(suffix):
            return filename[:-len(suffix)]
    return None


class BackendManager(DictMixin):
    """Responsible for loading backends.
    Backends don't need to be loaded explicitly. Just use the provided
    dictionary interface to access backends by name. Loading will happen
    automatically."""
    
    def __init__(self):
        """Creates a new backend manager."""
        self._loaded_cache = {}

    def _find_backends(self):
        """Finds all backends"""
        backends = []
        for path in config.directories:
            files = os.listdir(path)
            for fso in files:
                mod_name = get_backend_name(fso)
                if mod_name and mod_name not in backends:
                    backends.append(mod_name)
        return backends

    def _load_backend(self, backend, force=False):
        """Loads `backend`. Tries to get loaded backend from internal cache,
        unless force is True."""
        if backend not in self._loaded_cache or force:
            mod_name = BACKEND_MODULE_PATTERN % backend
            desc = imp.find_module(mod_name, config.backend_directories)
            try:
                module = imp.load_backend(mod_name, *desc)
            finally:
                # close the file object opened by find_module
                desc[0].close()
            if not self._check_module(module):
                raise ImportError(_(u'Invalid backend %s') % backend)
            else:
                self._loaded_cache[backend] = module
                return module
        return self._loaded_cache[backend]

    def _check_module(self, module):
        """Checks `module`. Returns False, if `module` is not valid
        backend"""
        return hasattr(module, '__phonebook_class__')

    def __getitem__(self, name):
        try:
            return self._load_backend(name)
        except ImportError:
            raise KeyError(_(u'No backend "%s" found') % name)

    def __iter__(self):
        return iter(self._find_backends())

    def __contains__(self, item):
        return item in self._find_backends()

    def iteritems(self):
        for backend in self._find_backends():
            try:
                yield (backend, self[backend])
            except KeyError:
                continue

    def itervalues(self):
        for backend in self._find_backends():
            try:
                yield self[backend]
            except KeyError:
                continue

    def backend_for_file(self, filename):
        """Returns a backend, which supports `filename`"""
        for backend in self:
            try:
                if self[backend].supports(filename):
                    return self[backend]
            except AttributeError:
                # backend doesn't define "support"
                pass
        return None


# create the global manager instance
_global_manager = BackendManager()


def manager():
    """Returns a global manager instance"""
    return _global_manager

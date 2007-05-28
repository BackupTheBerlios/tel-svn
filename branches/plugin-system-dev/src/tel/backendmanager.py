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


__revision__ = '$Id$'


import os
import imp

from UserDict import DictMixin

from tel import config


MODULE_SUFFIXES = zip(*imp.get_suffixes())[0]


def get_module_name(filename):
    """If `filename` is a module"""
    for suffix in MODULE_SUFFIXES:
        if filename.endswith(suffix):
            return filename[:-len(suffix)]
    return None


class BackendManager(DictMixin):
    """Responsible for loading backends.

    Supports dictionary interface for getting backends"""
    
    def __init__(self):
        """Creates a new backend manager."""
        self.backends = self._find_backends()
        self._loaded_cache = {}

    def _find_backends(self):
        """Finds all backends"""
        backends = []
        for path in config.directories:
            files = os.listdir(path)
            for fso in files:
                mod_name = get_module_name(fso)
                if mod_name and mod_name not in backends:
                    backends.append(mod_name)
        return backends

    def _load_backend(self, backend, force=False):
        """Loads `backend`. Tries to get loaded backend from internal cache,
        unless force is True."""
        if backend not in self._loaded_cache or force:
            desc = imp.find_module(backend, config.backend_directories)
            try:
                module = imp.load_backend(backend, *desc)
            finally:
                # close the file object opened by find_module
                desc[0].close()
            self._loaded_cache[backend] = module
            return module
        return self._loaded_cache[backend]

    def __getitem__(self, name):
        return self._load_backend(name)

    def __iter__(self):
        return iter(self.backends)

    def __contains__(self, item):
        return item in self.backends

    def iteritems(self):
        return ((backend, self[backend]) for backend in self.backends)

    def itervalues(self):
        return (self[backend] for backend in self.backends)

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


import os
import imp
from glob import glob


def get_module_description(filename):
    """Return description for `filename` or None, if `filename` is not a
    python module"""
    if os.path.isfile(filename):
        for desc in imp.get_suffixes():
            if filename.endswith(desc[0]):
                return desc
    return None


def get_module_name(filename):
    """Returns the module name for `filename`"""
    return os.path.splitext(os.path.basename(filename))[0]
            

def load_module(filename, name=None):
    """Loads module from `filename` as `name`. If `name` is None,
    it is determined from `filename`."""
    desc = get_module_description(filename)
    if desc:
        name = name or get_module_name(filename)
        stream = open(filename, desc[1])
        module = imp.load_module(name, stream, filename, desc)
        stream.close()
        return module
    else:
        return None


class BackendException(Exception):
    def __init__(self, msg, module):
        self.message = msg
        self.module = module


class BackendWrapper:
    """Provides safe access to a backend. Wraps exceptions to
    make sure, that mis-formatted plugins don't blow tel."""

    def __init__(self, backend_module):
        """Creates a new wrapper for `backend_module`"""
        self.backend = backend_module
        try:
            self.name = self.backend.NAME
            self.supports_files = self.backend.SUPPORTS_FILES
            self.supported_fields = self.backend.SUPPORTED_FIELDS
            self.default_filename = self.backend.DEFAULT_FILENAME
            self.supports_read = hasattr(self.backend, 'reader')
            self.supports_write = hasattr(self.backend, 'writer')
            # check, if backend has a supports method
            getattr(self.backend, 'supports')
        except AttributeError:
            raise BackendException('Invalid backend', self.backend)

    def reader(self, path=None):
        if not self.supports_read:
            raise BackendException('Backend doesn\'t support reading',
                                   self.backend)
        if self.supports_files:
            return self.backend.reader(path)
        else:
            if path is not None:
                raise BackendException('Backend doesn\'t support files',
                                       self.backend)
            else:
                return self.backend.reader()
        
    def writer(self, path=None):
        if not self.supports_write:
            raise BackendException('Backend doesn\'t support writing',
                                   self.backend)
        if self.supports_files:
            return self.backend.writer(path)
        else:
            if path is not None:
                raise BackendException('Backend doesn\'t support files',
                                       self.backend)
            else:
                return self.backend.writer()

    def supports(self, path):
        return self.backend.supports(path)
            


class BackendManager:
    """Responsible for loading backends"""
    def __init__(self, backend_directories=None):
        """Creates a new backend manager.
        :param backend_path: A path or a list of path names denoted
        directories to load backends from. If None, tel.CONFIG.backend_path
        is used"""
        self.backends = None
        self.backend_directories = backend_directories
        if not self.backend_directories:
            self.backend_directories = tel.CONFIG.backend_path
        if isinstance(self.backend_directories, basestring):
            self.backend_directories = [self.backend_directories]

        print 'backend directories', self.backend_directories

        self.load_backends()

    def load_backends(self):
        """Loads backends"""
        self.backends = {}
        imported = []
        for path in self.backend_directories:
            print 'searching in', path
            print os.listdir(path)
            files = os.listdir(path)
            print 'found', files
            for fso in files:
                filename = os.path.join(path, fso)
                name = get_module_name(filename)
                if name not in imported:
                    print 'importing', filename
                    module = load_module(filename, name)
                    if module is not None:
                        try:
                            imported.append(name)
                            wrapper = BackendWrapper(module)
                            self.backends[wrapper.name] = wrapper
                        except BackendException:
                            # ignore mis-formatted backends
                            pass
                    
    def get_backend(self, name):
        """Return the backend called `name`.
        :raises KeyError: If `name` is not found"""
        return self.backends[name]

    def find_backend_for_file(self, filename):
        """Return a appropriate backend for `filename` or None,
        if `filename` is not supported by any backend"""
        for backend in self.backends.itervalues():
            if backend.supports(filename):
                return backend
        return None

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tel install script
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
# DEALINGS IN THE SOFTWARE."""

import appdistutils

def get_version():
    filename = 'src/tel.py'
    stream = open(filename)
    for line in stream:
        if line.startswith('__version__'):
            stream.close()
            exec line
            return __version__
        elif line.startswith('import'):
            raise SystemExit('Couldn\'t extract version information')
        

long_description = """\
tel is a little console-based phone book program. It allows adding,
modifing, editing and searching of phone book entries right on your
terminal. Pretty printing capabilites are also provided.
Entries are stored in simple csv file. This eases import and export with
common spread sheet applications like Microsoft Excel or OpenOffice.org
Calc."""


import optparse
# get the real source file, not the compiled one
optparse_source = optparse.__file__.rstrip('c')


tel_sources = ['src/tel.py',
               'src/backendmanager.py',
               'src/phonebook.py',
               'src/consoleiface.py',
               'src/teltypes.py',
               'src/cmdoptparse.py',
               'src/backend.py',
               'src/backends/']


appdistutils.setup(name='tel',
                   version=get_version(),
                   description='A little terminal phone book',
                   long_description=long_description,
                   author='Sebastian \'lunar\' Wiesner',
                   author_email='basti.wiesner@gmx.net',
                   url='http://tel.berlios.de',
                   license='MIT/X11',
                   links=[('tel', 'tel.py')],
                   configurable=['src/tel.py'],
                   appmodules=tel_sources,
                   po=tel_sources + [optparse_source],
                   )

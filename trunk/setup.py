#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import os
import sys
import optparse

from distutils.filelist import FileList
from appdistutils import setup

sys.path.insert(0, os.path.abspath('./src'))
from tel import config


long_description = """\
tel is a little console-based phone book program. It allows adding,
modifing, editing and searching of phone book entries right on your
terminal. Pretty printing capabilites are also provided.
Entries are stored in simple csv file. This eases import and export with
common spread sheet applications like Microsoft Excel or OpenOffice.org
Calc."""


# gettext source file for i18n
optparse_source = optparse.__file__.rstrip('c')

# collect all python sources for i18n
tel_sources = FileList()
tel_sources.findall('./src')
tel_sources.include_pattern('*.py', anchor=False)


setup(name='tel',
      version=config.version,
      description='A little terminal phone book',
      long_description=long_description,
      author='Sebastian Wiesner',
      author_email='basti.wiesner@gmx.net',
      url='http://tel.lunaryorn.de',
      license='MIT/X11',
      # list packages
      packages=['tel'],
      package_dir={'': 'src'},
      package_data={'tel': ['backends/*.py']},
      # scripts
      scripts=[('src/tel_console.py', 'tel')],
      # i18n
      po_dir='po',
      po={'tel': tel_sources.files + [optparse_source]},
      )

#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """\
Copyright (c) 2007 Sebastian Wiesner

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the \"Software\"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE."""

"""executable script, which also contains global configuration"""

__revision__ = '$Id$'
__version__ = '0.1.6'
__authors__ = ['Sebastian Wiesner <basti.wiesner@gmx.net>']

import os
import sys


CONFIG_DIR = os.path.expanduser(os.path.join('~', '.tel'))
DEF_FILENAME = os.path.join(CONFIG_DIR, 'phonebook.csv')   


class _Config:
    # these get replaced with proper paths on setup.py install
    MESSAGES = '${install_messages}'
    APPMODULES = '${install_app_modules}'
    APPDATA = '${install_app_data}'


CONFIG = _Config()
sys.path.append(CONFIG.APPMODULES)


if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)

if __name__ == '__main__':
    # tel modules
    from consoleiface import ConsoleIFace
    ConsoleIFace().start()

# -*- coding: utf-8 -*-
# init file for tel package

"""This package provides all classes of tel"""

__revision__ = '$Id: tel.py 126 2007-04-03 11:37:39Z lunar $'

__license_name__ = 'MIT/X11'
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

__version__ = '0.2.0-pre1'
__authors__ = ('Sebastian Wiesner <basti.wiesner@gmx.net>',
               'Remo Wenger <potrmwn@gmail.com>')


from configuration import Configuration


# create a global configuration object
config = Configuration()


# adjust sys.path to include the tel package
sys.path.insert(0, config.appmodules)

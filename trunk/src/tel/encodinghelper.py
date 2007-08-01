#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2006-2007 Gerold Penz <gerold.penz@tirol.utanet.at>
# Copyright (c) 2007 Sebastian Wiesner <basti.wiesner@gmx.net>

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# see http://gelb.bcom.at/trac/misc/wiki/Encodinghelper for original sources


"""
Attempts to redirect stdout appropriatly to the current encoding. This makes
special chars appear correctly on text console.

This module attempts to identify the current encoding according to different
platforms. If encoding was successfully identified, stdout is redirected
through a codecs.DataWriter.
"""


__revision__ = "$Id$"



import sys
import codecs
import subprocess


def _read_locale():
    """Asks the 'locale' command on unix like systems"""
    process = subprocess.Popen(['locale'], stdout=subprocess.PIPE)
    process.wait()
    for line in process.stdout:
        line = line.strip()
        if line.startswith('LC_MESSAGES'):
            return line.split('=')[1]


def _get_encoding(outputstream):
    """Tries to determine encoding of standard output"""
    enc = (getattr(outputstream, "encoding", None) or
           sys.getfilesystemencoding())
    if not enc:
        # if it's still not identified
        plat = sys.platform
        if plat.startswith("win"):
            enc = "cp850"
        elif plat.startswith(("linux", "aix")):
            # try to read locale output
            enc = _read_locale()
        elif plat.startswith("cygwin"):
            enc = "raw_unicode_escape"
        else:
            enc = ""
    if enc.upper() in ("ASCII", "US-ASCII", "ANSI_X3.4-1968", "POSIX"):
        enc = ""
    return enc


stdout_encoding = _get_encoding(sys.stdout)
stderr_encoding = _get_encoding(sys.stderr)
stdin_encoding = _get_encoding(sys.stdin)

stdout = codecs.getwriter(stdout_encoding)(sys.stdout)
stderr = codecs.getwriter(stderr_encoding)(sys.stderr)
stdin = codecs.getreader(stdin_encoding)(sys.stdin)

# preserve old raw_input in this module namespace
no_encoding_raw_input = raw_input

def raw_input(prompt=None):
    """A raw_input variant, which is encoding aware"""
    if prompt:
        prompt = prompt.encode(stdout_encoding)
    retval = no_encoding_raw_input(prompt)
    return retval.decode(stdin_encoding)

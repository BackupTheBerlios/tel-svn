#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2006-2007 Gerold Penz <gerold.penz@tirol.utanet.at>
# Copyright (c) 2007 Sebastian Wiesner <basti.wiesner@gmx.net>

# Unlike the rest of tel, which is subject to the terms of MIT License as
# denoted in the file headers, this code is placed under public domain and
# may therefore be used without any restrictions by anyone.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# Based on Gerold Penz' encodinghelper.py
# http://gelb.bcom.at/trac/misc/wiki/Encodinghelper


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


_no_encoding_raw_input = raw_input

def raw_input(prompt=''):
    """A raw input function, that returns unicode objects decoded according
    to stdin_encoding"""
    value = _no_encoding_raw_input(prompt)
    return value.decode(stdin_encoding)


def redirect_std_streams(replace_raw_input=True):
    """Redirects output stream.

    **Note**: sys.stdin isn't currently redirected, as this breaks with
    raw_input. As a workaround you can set `replace_raw_input` to True,
    which will replace raw_input with an implementation, that returns
    unicode strings.

    The original raw_input function will still be available from this module
    as _no_encoding_raw_input"""
    # Only execute _outside_ idle
    if "idlelib" not in sys.modules:
        # redirect standard output stream
        if stdout_encoding:
            sys.stdout = codecs.getwriter(stdout_encoding)(sys.stdout)
        if stderr_encoding:
            sys.stderr = codecs.getwriter(stderr_encoding)(sys.stderr)
        ## if stdin_encoding:
        ##     sys.stdin = codecs.getreader(stdin_encoding)(sys.stdin)
        if replace_raw_input:
            import __builtin__
            __builtin__.__dict__['raw_input'] = raw_input

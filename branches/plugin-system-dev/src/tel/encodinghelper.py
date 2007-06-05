#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2006-2007 Gerold Penz <gerold.penz@tirol.utanet.at>
# This code is public domain

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
        elif any((plat.startswith(p) for p in ("linux", "aix"))):
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
stdin_encoding = _get_encoding(sys.stdin)


def redirect_std_streams():
    """Redirects output stream.

    **Note**: sys.stdin isn't currently redirected, as this breaks with
    raw_input"""
    # Only execute _outside_ idle
    if "idlelib" not in sys.modules:
        # redirect standard output stream
        if stdout_encoding:
            sys.stdout = codecs.getwriter(stdout_encoding)(sys.stdout)
        ## if stdin_encoding:
        ##     sys.stdin = codecs.getreader(stdin_encoding)(sys.stdin)

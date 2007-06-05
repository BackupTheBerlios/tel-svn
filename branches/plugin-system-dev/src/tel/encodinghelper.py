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


import os
import sys
import codecs
import subprocess


def _read_locale():
    """Asks the 'locale' command on unix like systems"""
    process = subprocess(['locale'], stdout=subprocess.PIPE)
    process.wait()
    for line in process.stdout:
        line = line.strip()
        if line.startswith('LC_MESSAGES'):
            return line.split('=')[1]


def _get_encoding(outputstream):
    """Tries to determine encoding of standard output"""
    out_enc = (getattr(outputstream, "encoding", None) or
               sys.getfilesystemencoding())
    if not out_enc:
        # if it's still not identified
        plat = sys.platform
        if plat.startswith("win"):
            out_enc = "cp850"
        elif any((plat.startswith(p) for p in ("linux", "aix"))):
            # try to read locale output

        elif plat.startswith("cygwin"):
            out_enc = "raw_unicode_escape"
        else:
            out_enc = ""
    if out_enc.upper() in ("ASCII", "US-ASCII", "ANSI_X3.4-1968", "POSIX"):
        out_enc = ""
    return out_enc


stdout_encoding = _get_encoding(sys.stdout)
stdin_encoding = _get_encoding(sys.stdin)


def redirect_stream():
    """Redirects output stream"""
    # Only execute _outside_ idle
    if "idlelib" not in sys.modules:
        # redirect standard output stream
        if stdout_encoding:
            sys.stdout = codecs.getwriter(stdout_encoding)(sys.stdout)
        if stdin_encoding:
            sys.stdin = codecs.getreader(stdin_encoding)(sys.stdin)

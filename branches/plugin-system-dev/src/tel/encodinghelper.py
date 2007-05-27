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
 

import os
import sys
import codecs
import subprocess


def _istrue(function, iterable):
    """
    Helper function which returns True, if `function` returned True for
    every element in `iterable`.
    """
    for value in iterable:
        if function(value):
            return True
    return False


# Only execute _outside_ idle
if "idlelib" not in sys.modules:
    # determine out_enc from standard values
    out_enc = (getattr(sys.stdout, "encoding", None) or
               sys.getfilesystemencoding())
    if not out_enc:
        # if it's still not identified
        plat = sys.platform
        if plat.startswith("win"):
            out_enc = "cp850"
        elif _istrue(plat.startswith, ("linux", "aix")):
            # try to read locale output
            process = subprocess(['locale'], stdout=subprocess.PIPE)
            process.wait()
            for line in process.stdout:
                line = line.strip()
                if line.startswith('LC_MESSAGES'):
                    out_enc = line.split('=')[1]
                    break              
        elif plat.startswith("cygwin"):
            out_enc = "raw_unicode_escape"
        else:
            out_enc = ""
    if out_enc.upper() in ("ASCII", "US-ASCII", "ANSI_X3.4-1968", "POSIX"):
        out_enc = ""
    if out_enc:
        sys.stdout = codecs.getwriter(out_enc)(sys.stdout)

    # TODO: Do we need this?
    ##
    ## STDIN
    ##
    #if _stdin_encoding.lower() == "none":
        #pass
    #elif _stdin_encoding.lower() == "auto":
        ## sys.stdin umleiten, damit Umlaute korrekt eingelesen werden.
        ## Dafür wird zuerst herausgefunden mit welcher Platform man es zu tun hat und
        ## danach wird, abhängig von der Platform, versucht das Encoding heraus zu finden.
        #in_enc = ""
        #plat = sys.platform
        #if plat.startswith("win"):
            #in_enc = getattr(sys.stdin, "encoding", None) or \
                #sys.getfilesystemencoding() or "mbcs"
            ##if in_enc == "mbcs":
            ##    in_enc = "cp850"
        #elif _istrue(plat.startswith, ("linux", "aix")):
            #in_enc = getattr(sys.stdin, "encoding", None) or \
                #sys.getfilesystemencoding() or \
                #os.popen("locale | grep 'LC_MESSAGES'").read().strip().split("=")[1]
        #elif _istrue(plat.startswith, ("cygwin",)):
            #in_enc = getattr(sys.stdin, "encoding", None) or \
                #sys.getfilesystemencoding() or "raw_unicode_escape"
        #else:
            #in_enc = getattr(sys.stdin, "encoding", None) or \
                #sys.getfilesystemencoding() or ""
        #if in_enc.upper() in ("ASCII", "US-ASCII", "ANSI_X3.4-1968", "POSIX"):
            #in_enc = ""
        #if in_enc:
            #sys.stdin = codecs.getreader(in_enc)(sys.stdin)
    #else:
        #sys.stdin = codecs.getreader(_stdin_encoding)(sys.stdin)

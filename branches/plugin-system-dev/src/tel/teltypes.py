# -*- coding: utf-8 -*-
# teltypes: defines field types
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


"""This modules defines additional types for fields"""


__revision__ = '$Id$'


import re


class email(unicode):
    """Represents a mail address.

    :ivar user: contains the user part of the mail address
    :ivar domain: contains the mail domain
    :ivar pattern: regular expression to verify email addresses"""
    # simple mail address pattern
    pattern = re.compile(r'^(?P<user>[^@\s]+)@(?P<domain>[^@\s]+\.[\w]+)$')

    def __init__(self, *args):
        unicode.__init__(self, *args)
        if args:
            match = self.pattern.match(args[0])
            if match:
                self.__dict__.update(match.groupdict())
            else:
                raise ValueError('Invalid literal for email address: %s'
                                 % self)


class phone_number(unicode):
    """Represents a phone number.
    
    :ivar pattern: regular expression used to verify phone numbers"""
    # simple pattern to match phone numbers
    pattern = re.compile(r'^[-()/\d\s\W]+$')

    def __init__(self, *args):
        unicode.__init__(self, *args)
        if args and not self.pattern.match(args[0]):
            raise ValueError('Invalid literal for phone number: %s'
                             % self)
                

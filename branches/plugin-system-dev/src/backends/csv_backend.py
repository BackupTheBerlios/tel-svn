# -*- coding: utf-8 -*-
# csv backend for phonebook.py
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


import os
import csv

import phonebook


# a list of all fields supported by this file type
# if None, this file type supports all fields listed in phonebook.FIELDS
SUPPORTED_FIELDS = None

# if this filetype supports saving to files
# This will be True for the most types, but could be False for bindings to
# the KDE Addressbook for instance, since this is located at a fixed place
SUPPORTS_FILES = True

# the default filename for this file type. Only needs to be defined, if
# SUPPORTS_FILES is True
DEFAULT_FILENAME = 'phonebook.csv'

# The name of this backend... Used to specify this field on command line
NAME = 'csv'


def supports(path):
    """Checks, if `path` denotes a valid file for this filetype.
    :returns: True, if `path` is supported"""
    ext = os.path.splitext(path)[1]
    return ext.lower() == '.csv'


# note that, if SUPPORTS_FILES is False, these functions don't get a path
# specified
# If one of these functions is not implemented, reading or writing will be
# disabled
def reader(path):
    """Return a reader for `path`"""
    return CSVReader(path)

def writer(path):
    return CSVWriter(path)


# Writer objects must support at least two methods:
# write_entry(entry) and close

class CSVWriter:
    def __init__(self, path):
        """The `path` to write to"""
        self.filename = path
        self.stream = open(self.filename, 'wb')
        self.writer = csv.writer(stream)
        self.writer.writerow(phonebook.FIELDS)


    def write_entry(self, entry):
        """Write `entry` to the file"""
        row = [unicode(entry[field]).encode('utf-8') for field in
               phonebook.FIELDS]
        writer.writerow(row)

    def close(self):
        self.stream.close()

# Reader objects must support iteration over Entry objects and a close
# method

class CSVReader:
    def __init__(self, path):
        self.filename = path
        self.stream = open(self.filename, 'rb')
        self.reader = csv.DictReader(self.stream)

    def close(self):
        self.stream.close()

    def __iter__(self):
        for row in self.reader:
            entry = phonebook.Entry()
            for k in row:
                entry[k] = row[k].decode('utf-8')
            yield entry

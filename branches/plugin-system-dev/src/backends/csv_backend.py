# -*- coding: utf-8 -*-
# csv backend for tel
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


from __future__ import with_statement


__revision__ = '$Id$'


import os
import csv

from tel.phonebook import Entry, Phonebook
from tel import config


_ = config.translation.ugettext


__long_description__ = _("""\
A simple backend, which uses classic excel-style csv (comma separated
values) files to store entries.
""")
__short_description__ = _('A csv-based backend')


# Modules, that don't define this function are never loaded for
# non-absolute uris
def supports(path):
    """Checks, if `path` denotes a valid file for this filetype.
    :returns: True, if `path` is supported"""
    ext = os.path.splitext(path)[1]
    return ext.lower() == '.csv'


class CsvPhonebook(Phonebook):
    def load(self):
        """Load entries."""
        self.clear()
        with open(self.uri.location, 'rb') as stream:
            self.reader = csv.DictReader(stream)
            for row in self.reader:
                entry = Entry()
                for k in row:
                    val = row[k].decode('utf-8')
                    try:
                        entry[k] = val
                    except KeyError:
                        pass
                self.add(entry)

    def save(self):
        """Save entries."""
        with open(self.uri.location, 'wb') as stream:
            writer = csv.writer(stream)
            writer.writerow(self.supported_fields())
            for entry in self:
                row = [unicode(entry[field]).encode('utf-8') for field in
                       self.supported_fields()]
                writer.writerow(row)


__phonebook_class__ = CsvPhonebook

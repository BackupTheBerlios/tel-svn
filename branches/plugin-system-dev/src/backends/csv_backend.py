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


__revision__ = '$Id$'


import os
import csv


import backend


# Use this for backends, which are part of the upstream releases
_ = backend._

# use __entry_storage__ attribute, if your storage class is not named
# EntryStorage
# use __supported_fields__ if your backend does only support a limited
# subset of phonebook.FIELDS

# The name of this backend... Used to specify this field on command line
__backend_name__ = 'csv'


def supports(path):
    """Checks, if `path` denotes a valid file for this filetype.
    :returns: True, if `path` is supported"""
    ext = os.path.splitext(path)[1]
    return ext.lower() == '.csv'


class EntryStorage(backend.DictStorage):
    def load(self):
        """Load entries."""
        self.stream = open(self.uri, 'rb')
        self.reader = csv.DictReader(self.stream)
        for row in self.reader:
            entry = self.create_new()
            for k in row:
                val = row[k].decode('utf-8')
                if val == '':
                    val = empty
                entry[k] = val
            self[None] = entry
        self.stream.close()

    def save(self):
        """Save entries."""
        stream = open(self.uri, 'wb')
        writer = csv.writer(stream)
        writer.writerow(backend.FIELDS)
        for entry in self:
            row = [unicode(entry[field]).encode('utf-8') for field in
                   backend.FIELDS]
            writer.writerow(row)
        stream.close()

    def create_new(self):
        entry = backend.StandardEntry()
        index = self._lowest_free_index()
        entry['index'] = index
        self.entries[index] = entry
        return entry

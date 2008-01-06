# -*- coding: utf-8 -*-
# kaddressbook backend
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

__revision__ = '$Id$'


import qt
from kabc import KABC as kabc

from tel.phonebook import Entry, Phonebook, NoSuchField, field_type
from tel import teltypes


class KABCEntry(Entry):
    """Wraps a KABC::Addressee object"""
    # maps tel fields to corresponding methods of a kabc entry object
    addressee_mapping = {
        'nickname': 'nickName',
        'firstname': 'givenName',
        'lastname': 'familyName',
        'title': 'title',
        'birthday': 'birthday',
    }

    # maps tel fields to corresponding methods of a kabc address object
    address_mapping = {
        'street': 'street',
        'postcode': 'postalCode',
        'town': 'locality'
        'country': 'country',
        'pob': 'postOfficeBox',
    }

    def __init__(self):
        self.kabc_entry = None

    def __setitem__(self, field, value):
        raise NotImplementedError()

    def __getitem__(self, field):
        value = self._get_value()
        # perform proper type conversion
        if isinstance(value, qt.Datetime):
            date = value.date()
            return teltypes.date(date.year(), date.month(), date.day())
        else:
            return field_type(field)(value)

    def _get_value(self, field):
        if field not in KABCPhonebook.supported_fields():
            raise NoSuchField(field)
        # get mapping, if the field can be mapped
        if field in self.addressee_mapping:
            method = getattr(self.kabc_entry,
                             self.addressee_mapping[field])
            return method()
        elif field in self.address_mapping:
            addresses = self.kabc_entry.addresses()
            if addressess:
                address = addressess[0]
                method = getattr(addressess[0], self.address_mapping[field])
                return method()
            else:
                return ''
        else:
            # field cannot be mapped, so invoke the corresponding method
            return getattr(self, 'get_' + field)

    def get_email(self):
        mails = self.kabc_entry.emails()
        return (mails[0] if mails else '')

    def get_mobile(self):
        return self.kabc_entry.phoneNumber(kabc.PhoneNumber.Cell).number()

    def get_phone(self):
        return self.kabc_entry.phoneNumber(kabc.PhoneNumber.Home).number()

    def keys(self):
        return KABCPhonebook.supported_fields()

    def setdefault(self, field, default=None):
        raise NotImplementedError()


class KABCPhonebook(Phonebook):
    fields = ('title', 'firstname', 'lastname', 'nickname', 'street',
              'postcode', 'town', 'country', 'pob', 'mobile', 'phone',
              'email', 'birthday')

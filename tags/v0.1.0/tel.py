#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2007 Sebastian Wiesner
# 
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import sys
import csv
import gettext
_ = gettext.gettext

from optparse import OptionParser

# The directory, where tel stores its config
CONFIG_DIR = os.path.expanduser(os.path.join('~', '.tel'))
# the default phonebook
DEF_FILENAME = os.path.join(CONFIG_DIR, 'phonebook.csv')


class Entry:
    """This class stores a single adress entry.

    :ivar firstname:
    :ivar lastname:
    :ivar street:
    :ivar postcode:
    :ivar town:
    :ivar mobile:
    :ivar phone:
    :ivar email:
    :ivar birthdate:
    """

    # this is a list of all supported fields. It is used be the search
    # method to iterate over all known fields
    known_fields = ('firstname', 'lastname', 'street', 'postcode', 'town',
                    'mobile', 'phone', 'email', 'birthdate')
                    

    def __init__(self):
        # init all fields
        for field in Entry.known_fields:
            setattr(self, field, None)

    def __str__(self):
        # print a pretty representation
        msg = [_('Name: %(firstname)s %(lastname)s'),
               _('Street: %(street)s'),
               _('Town: %(postcode)s %(town)s'),
               _('Phone: %(phone)s'),
               _('Mobile: %(mobile)s'),
               _('EMail: %(email)s'),
               _('Date of birth: %(birthdate)s')]
        print '\n'.join(msg) % self.__dict__

    def __cmp_string(self):
        # this is the string used for comparision of two entries
        return '%(lastname)s, %(firstname)s' % self.__dict__

    def __cmp__(self, other):
        if self.__cmp_string() < other.__cmp_string():
            return -1
        elif self.__cmp_string() == other.__cmp_string():
            return 0
        else:
            return 1

    def __hash__(self):
        return hash(self.lastname) ^ (self.firstname)

    def matches(self, pattern):
        """:returns: True, if any field in this entry matches `pattern`,
        False otherwise"""
        for field in Entry.known_fields:
            if pattern in getattr(self, field):
                return True
        return False


class PhoneBook:
    """This class provides an interface to the phone book

    :ivar entries: A list of all Address entries in this phone book.
    :ivar path: The file, from which this Phonebook was loaded.
    """

    def __init__(self, path):
        """Creates a PhoneBook from the file denoted by `path`, which
        defaults to ~/.tel/phonebook.csv."""
        self.entries = None
        self.path = path
        self.load()

    def __del__(self):
        self.save()

    def load(self):
        """Loads the phone book from the file.
        **WARNING:** This resets the `entries` list. All changes made after
        the last invocation of _`save()` will be lost"""
        self.entries = []
        reader = csv.reader(open(self.path, 'rb'))
        for row in reader:
            entry = Entry()
            entry.firstname = row[0]
            entry.lastname = row [1]
            entry.street = row[2]
            entry.postcode = row[3]
            entry.town = row[4]
            entry.mobile = row[5]
            entry.phone = row[6]
            entry.email = row[7]
            entry.birthdate = row[8]
            self.entries.append(entry)
        self.entries.sort()

    def save(self):
        """Writes the phone book back to the file"""
        self.entries.sort()
        stream = open(self.path, 'wb')
        writer = csv.writer(stream)
        for entry in self.entries:
            writer.writerow([entry.firstname,
                             entry.lastname,
                             entry.street,
                             entry.postcode,
                             entry.town,
                             entry.mobile,
                             entry.phone,
                             entry.email,
                             entry.birthdate])
        stream.close()

    def search(self, pattern):
        """Searchs the phone book for `pattern`.
        :returns: A list of entries which match the pattern"""
        found_entries = []
        for entry in self.entries:
            if entry.matches(pattern):
                found_entries.append(entry)
        return found_entries

    def decrypt(self):
        """Decrypts phonebook"""
        # TODO implement
        pass

    def encrypt(self):
        # TODO implement
        """Encrypts phonebook"""


class ConsolePhoneBook(PhoneBook):
    """Provides console access to a PhoneBook.
    Users can interactively edit the phone book"""

    def __init__(self, path):
        """Creates a new instance"""
        PhoneBook.__init__(self, path)

    def create_interactive(self):
        """Creates a new entry. Allows the users to interactively enter all
        values"""

        entry = Entry()
        print _('Please fill the following fields. To leave a field empty,'
                'just press ENTER without entering something.')
        print
        entry.firstname = raw_input(_('First name: '))
        entry.lastname = raw_input(_('Last name: '))
        entry.street = raw_input(_('Street and street number: '))
        entry.postcode = raw_input(_('Postal code: '))
        entry.town = raw_input(_('Town'))
        entry.mobile = raw_input(_('Mobile'))
        entry.phone = raw_input(_('Phone'))
        entry.email = raw_input(_('EMail'))
        entry.birthdate = raw_input(_('Date of birth'))
        print _('Thanks. The entry is now saved ...')
        self.entries.append(entry)

    def print_short_list(self, entries=None):
        """Prints all `entries` in the following format:
        [index] -- Last name, First name
        If `entries` is None, all entries are printed"""
        if not entries:
            entries = self.entries
        for i in xrange(entries):
            msg = '[%s] -- %%(lastname)s, %%(firstname)s' % i
            print msg % self.entries[i].__dict__

    def print_long_list(self, entries=None):
        """Prints every single entry in `entries` in full detail.
        If `entries` is None, all entries are printed"""
        if not entries:
            entries = self.entries
        for entry in entries:
            print str(entry)
            print '-'*20

    def search(self, pattern):
        """Searches phone book for 'pattern' and print matching entries"""
        matching = PhoneBook.search(self, pattern)
        self.print_long_list(matching)

    def show(self, index):
        """Prints the entry at `index`"""
        print str(self.entries[index])
        

__description__ = _('With Tel you can create little phonebooks in csv '
                  'format.')
__version__ = '0.07.0'

# a list of all commands, Tel supports for viewing and manipulating the
# phone book
__commands__ = [('list', _('Prints a short list of all entries')),
                ('print', _('Prints all entries in full detail')),
                ('show INDEX', _('Shows the entry at INDEX. INDEX is the '
                                 'same as displayed by the \'list\' '
                                 'command.')),
                ('search PATTERN', _('Searches the phone book for PATTERN '
                                     'and prints all matching entries')),
                ('create', _('Creates a new entry. Please fill the '
                             'displayed fields.'))]

def print_commands():
    """Prints a list of all available commands"""
    print _('Available commands')
    maxlen = max([len(item[0]) for item in __commands__])
    for item in __commands__:
        print ' ', item[0].ljust(maxlen), ' ', item[1]
  
def parse_args():
    """Parses cmd line arguments"""
    usage = '%prog -f|--file FILE command'
    parser = OptionParser(usage=usage, description=__description__,
                          version=__version__)
    parser.set_defaults(file=DEF_FILENAME)
    parser.add_option('-f', '--file', action='store', dest='file',
                      help='Use FILE as phone book')
    parser.add_option('--help-commands', action='store_true',
                      dest='commands',
                      help='Print information about available commands')
    (options, args) = parser.parse_args()

    if options.commands:
        print_commands()
        sys.exit()
    
    if not args:
        parser.error(_('Please specify a command'))
    command = args[0]
    args = args[1:]
    return (options, command, args)
        

def main():
    """Main function"""
    (options, command, args) = parse_args()
    phone_book = ConsolePhoneBook(path=options.file)

    # execute the specified command
    if command == 'list':
        phone_book.print_short_list()
    elif command == 'print':
        phone_book.print_long_list()
    elif command == 'show':
        try:
            phone_book.show(int(args[0]))
        except IndexError:
            sys.exit(_('No valid index specified'))
    elif command == 'create':
        phone_book.create_interactive()
        phone_book.save()
    elif command == 'search':
        try:
            pattern = args[0]
            phone_book.search(pattern)
        except IndexError:
            sys.exit(_('Please give me a pattern to search.'))
    elif command == 'delete':
        pass # TODO: implement
    elif command == 'decrypt':
        pass # TODO: implement
    elif command == 'encrypt':
        pass # TODO: implement
    

if __name__ == '__main__':
    main()
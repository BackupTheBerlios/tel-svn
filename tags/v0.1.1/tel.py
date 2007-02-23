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

# Tel version
__version__ = '0.1.1'

import os
import sys
import csv
import inspect
import gettext
import itertools
_ = gettext.gettext

from optparse import OptionParser


# The directory, where tel stores its config
CONFIG_DIR = os.path.expanduser(os.path.join('~', '.tel'))
# the default phonebook
DEF_FILENAME = os.path.join(CONFIG_DIR, 'phonebook.csv')


class Entry(object):
    """This class stores a single adress entry.
    
    :ivar index: a unique index (like a db primary key)
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
                  
    def __init__(self):
        # init all fields
        self.index = None
        self.firstname = None
        self.lastname = None
        self.street = None
        self.postcode = None
        self.town = None
        self.mobile = None
        self.phone = None
        self.email = None
        self.birthdate = None

    def __str__(self):
        # return a pretty representation
        msg = _('Index: %(index)i\n'
                'Name: %(firstname)s %(lastname)s\n'
                'Street: %(street)s\n'
                'Town: %(postcode)s %(town)s\n'
                'Phone: %(phone)s\n'
                'Mobile: %(mobile)s\n'
                'EMail: %(email)s\n'
                'Date of birth: %(birthdate)s') % self.__dict__
        return msg

    def __lt__(self, other):
        return NotImplemented

    def __le__(self, other):
        return NotImplemented

    def __gt__(self, other):
        return NotImplemented

    def __ge__(self, other):
        return NotImplemented

    def __ne__(self, other):
        for field in self._fields(self):
            if getattr(self, field) != getattr(other, field):
                return True
        return False

    def __eq__(self, other):
        return not self.__ne__(other)

    def __hash__(self):
        hash_ = 0
        for field in self._fields(self):
            hash_ ^= hash(getattr(self, field))
        return hash_

    def __repr__(self):
        # return a short representation
        return '[%(index)i] -- %(lastname)s, %(firstname)s' % self.__dict__

    def _fields(self):
        """:returns: A list of all fields"""
        fields = filter(lambda field: not field.startswith('_'),
                        self.__dict__.keys())
        return sorted(fields)

    def matches(self, pattern):
        """Note, that this method does *not* support regular expressions.
        :param pattern: A string pattern, which is searched in this entry
        :returns: True, if any field in this entry matches `pattern`,
        False otherwise"""
        for field in self._fields():
            # very simple searching algo ;)
            if field == 'index':
                try:
                    if int(pattern) == self.index:
                        return True
                except ValueError:
                    # ignore, if pattern is no integer
                    pass
            elif pattern in getattr(self, field):
                return True
        return False


class PhoneBook:
    """This class provides an interface to the phone book

    :ivar path: The file, from which this Phonebook was loaded.
    """

    def __init__(self, path):
        """Creates a PhoneBook from the file denoted by `path`, which
        defaults to ~/.tel/phonebook.csv."""
        self._entries = None
        self.path = path
        self.load()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._entries[key]
        elif isinstance(key, slice):
            raise NotImplementedError('__setitem__ not implemented for '
                                      'slices')
            # TODO support slice objects

    def __setitem__(self, key, value):
        if not isinstance(value, Entry):
            raise TypeError('PhoneBook only supports Entry objects')
        if not key:
            if value.index:
                # use the index of entry
                key = value.index
            else:
                # search a free index
                for i in itertools.count():
                    if i not in self._entries.keys():
                        key = i
                        break
        if isinstance(key, int):
            # make sure index and key are identical
            value.index = key
            self._entries[key] = value
        elif isinstance(key, slice):
            # TODO support slice objects
            raise NotImplementedError('__getitem__ not implemented for '
                                      'slices')

    def __delitem__(self, key):
        if isinstance(key, int):
            del self._entries[key]
        elif isinstance(key, slice):
            # TODO support slice objects
            raise NotImplementedError('__delitem__ not implemented for '
                                      'slices')

    def __iter__(self):
        # iterate over the values of _entries here, since the key is present
        # in Entry.index
        return iter(self._entries.values())

    def __contains__(self, item):
        if isinstance(item, int):
            # regard item as an index
            return item in self._entries
        elif isinstance(item, Entry):
            # regard item as an entry
            return item in self._entries.values()
        elif isinstance(item, basestring):
            return len(self.search(item)) > 0

    def load(self):
        """Loads the phone book from the file.
        **WARNING:** This resets the `entries` list. All changes made after
        the last invocation of _`save()` will be lost"""
        self._entries = {}
        if os.path.exists(self.path):
            reader = csv.DictReader(open(self.path, 'rb'))
            for row in reader:
                entry = Entry()
                for k in row:
                    setattr(entry, k, row[k])
                # make sure we have an integer as key
                entry.index = int(entry.index)
                self._entries[entry.index] = entry

    def save(self):
        """Writes the phone book back to the file"""
        stream = open(self.path, 'wb')
        fields = Entry()._fields()
        # write a head line containing the names of the fields
        writer = csv.writer(stream)
        writer.writerow(fields)
        # write all entries
        writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        for entry in self._entries.values():
            writer.writerow(entry.__dict__)
        stream.close()

    def add(self, entry):
        """Adds `entry` to the phone book. If the _index property of `entry`
        is None, then the index is autogenerated. If it already has a value,
        this value is used as index. Any entry, which has this index, is
        overwritten. You can use this behaviour to replace entries in the
        phone book"""
        self[entry.index] = entry

    def remove(self, entry):
        """Remove `entry`. If `entry` is an integer, it is assumed to be the
        index of the entry to remove. If `entry` is an instance of Entry,
        the property index is used as the index"""
        index = None
        if isinstance(entry, Entry):
            index = entry.index
        elif isinstance(entry, int):
            index = entry
        del self[index]

    def search(self, pattern):
        """Searchs the phone book for `pattern`.
        :returns: A list of entries which match the pattern"""
        found_entries = []
        for entry in self:
            if entry.matches(pattern):
                found_entries.append(entry)
        return found_entries

    def decrypt(self):
        """Decrypts phonebook"""
        # TODO implement
        pass

    def encrypt(self):
        """Encrypts phonebook"""
        # TODO implement
        pass


class ConsoleIFace:
    """Provides a console interface to Tel"""

    # some ideas
    # TODO: search command should accept an argument, which specifies the fields to search in
    # TODO: search could support regular expressions
    # TODO: show and print should accept an argument, which specifies the fields to show
    # TODO: if a search was only run over specific fields, only these fields should be printed
    # TODO: Mark fields, which where matched by the search pattern
    # TODO: implement encryption
    # TODO: support sorting for list, print and search commands

    usage = '%prog -f|--file FILE command'
    description = _('With Tel you can create little phonebooks in csv '
                    'format.')

    def __init__(self):
        self.phonebook = None

    def print_short_list(self, entries=None):
        """Prints all `entries` in a short format:
        If `entries` is None, all entries are printed"""
        if entries is None:
            entries = self.phonebook
        for entry in entries:
            print repr(entry)

    def print_long_list(self, entries=None):
        """Prints every single entry in `entries` in full detail.
        If `entries` is None, all entries are printed"""
        if entries is None:
            entries = self.phonebook
        for entry in entries:
            print str(entry)
            print '-'*20

    ## COMMANDS

    # All functions, that implement commands, start with the prefix '_cmd_'
    # The content of the property "help" of these functions is used as help
    # for --help-commands. Commands, which specifiy arguments, need to
    # perform type conversion for themselves. Arguments are always passed as
    # string

    # to add a new command 'test' with the parameter 'foo', just add a new
    # function here:
    #
    #   def _cmd_test(self, foo)
    #
    # To add a help string for the new command, just add a help property to
    # the function:
    #
    #  _cmd_test.help = _('Does nothing')
    #
    # Note: You should use gettext to support i18n for your documentation

    def _cmd_list(self):
        self.print_short_list()

    def _cmd_print(self):
        self.print_long_list()

    def _cmd_show(self, index):
        print self.phonebook[int(index)]

    def _cmd_search(self, pattern):
        self.print_long_list(self.phonebook.search(pattern))

    def _cmd_create(self):
        entry = Entry()
        print _('Please fill the following fields. To leave a field empty,'
                'just press ENTER without entering something.')
        print
        entry.firstname = raw_input(_('First name: '))
        entry.lastname = raw_input(_('Last name: '))
        entry.street = raw_input(_('Street and street number: '))
        entry.postcode = raw_input(_('Postal code: '))
        entry.town = raw_input(_('Town: '))
        entry.mobile = raw_input(_('Mobile: '))
        entry.phone = raw_input(_('Phone: '))
        entry.email = raw_input(_('EMail: '))
        entry.birthdate = raw_input(_('Date of birth: '))
        print _('Thanks. The entry is now saved ...')
        self.phonebook.add(entry)
        self.phonebook.save()

    _cmd_list.help = _('Lists all entries in short format')
    _cmd_print.help = _('Prints all entries in full detail')
    _cmd_show.help = _('Shows the entry at the specified INDEX. The index '
                       'is the same as printed by the list command')
    _cmd_search.help = _('Searches phone book for PATTERN and prints all '
                         'matching entries')
    _cmd_create.help = _('Creates a new entry')

    ## COMMAND support functions

    def _get_cmd_function(self, command):
        """Returns the function for `command`"""
        name = '_cmd_%s' % command
        function = getattr(self, name)
        return function

    def _get_cmd_declaration(self, command):
        """Returns the command declaration for `command`.
        The command foo with the argument bar would result in:
        foo BAR"""
        declaration = [command]
        function = self._get_cmd_function(command)
        # only the first list element is important, since we are currently
        # not interested in *args, **args and default values
        # NOTE: this may change in the future!
        argspec = inspect.getargspec(function)[0]
        for arg in argspec:
            # ignore the "self" argument of method declarations
            if arg != 'self':
                declaration.append(arg.upper())
        return ' '.join(declaration)

    def _get_cmd_help(self, command):
        """Returns the help for `command`"""
        return self._get_cmd_function(command).help

    def _get_cmd_list(self):
        """Returns a list of all known commands"""
        # find all command functions
        commands = filter(lambda element: element.startswith('_cmd_'),
                          ConsoleIFace.__dict__.keys())
        # strip the prefix from command functions
        return map(lambda element: element[5:], commands)

    def _print_commands_help(self):
        """Prints a list of all available commands and their documentation"""
        print _('Available commands:')
        commands = self._get_cmd_list()
        commands = [(self._get_cmd_declaration(cmd),
                     self._get_cmd_help(cmd)) for cmd in commands]
        maxlen = max([len(item[0]) for item in commands])
        for item in commands:
            print ' ', item[0].ljust(maxlen), ' ', item[1]

    def _parse_args(self):
        """Parses command line arguments"""
        parser = OptionParser(usage=self.usage,
                              description=self.description,
                              version=__version__)
        parser.set_defaults(file=DEF_FILENAME)
        parser.add_option('-f', '--file', action='store', dest='file',
                          help='Use FILE as phone book')
        parser.add_option('--help-commands', action='store_true',
                          dest='commands',
                          help='Print information about available commands')
        (options, args) = parser.parse_args()
        
        if options.commands:
            self._print_commands_help()
            sys.exit()
            
        if not args:
            parser.error(_('Please specify a command'))
        command = args[0]
        args = args[1:]
        return (options, command, args)

    def start(self):
        """Starts the interface"""
        try:
            (options, command, args) = self._parse_args()
            self.phonebook = PhoneBook(options.file)
            try:
                command = self._get_cmd_function(command)
            except AttributeError:
                sys.exit(_('Unknown command: %s') % command)
                # run the command with all specified arguments
            command(*args)
        except KeyboardInterrupt:
            sys.exit(_('Dying peacefully ...'))
    

if __name__ == '__main__':
    ConsoleIFace().start()

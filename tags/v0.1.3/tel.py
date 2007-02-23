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
__version__ = '0.1.3'

import os
import sys
import csv
import gettext
import itertools
import shutil
import re
_ = gettext.gettext

try:
    # more comfortable line editing
    import readline
except ImportError:
    pass

from optparse import (Option, OptionError, OptionParser, OptionValueError)

# some ideas
# TODO: implement encryption
# TODO: search command should accept an argument, which specifies the
#       fields to search in
# TODO: search could support regular expressions
# TODO: show and print should accept an argument, which specifies the
#       fields to show
# TODO: if a search was only run over specific fields, only these
#       fields should be printed
# TODO: Mark fields, which where matched by the search pattern
# TODO: support sorting for list, list-detail and search commands

# The directory, where tel stores its config
CONFIG_DIR = os.path.expanduser(os.path.join('~', '.tel'))
if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)
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
        msg = _('Index:          %(index)s\n'
                'Name:           %(firstname)s %(lastname)s\n'
                'Street:         %(street)s\n'
                'Town:           %(postcode)s %(town)s\n'
                'Phone:          %(phone)s\n'
                'Mobile:         %(mobile)s\n'
                'eMail:          %(email)s\n'
                'Date of birth:  %(birthdate)s') % self.__dict__
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
        for field in self._fields():
            if getattr(self, field) != getattr(other, field):
                return True
        return False

    def __eq__(self, other):
        return not self.__ne__(other)

    def __hash__(self):
        hash_ = 0
        for field in self._fields():
            hash_ ^= hash(getattr(self, field))
        return hash_

    def __repr__(self):
        # return a short representation
        return '[%(index)s] -- %(lastname)s, %(firstname)s' % self.__dict__

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
        raise NotImplementedError('Encryption is not yet supported')

    def encrypt(self):
        """Encrypts phonebook"""
        # TODO implement
        raise NotImplementedError('Encryption is not yet supported')


class CommandOption(Option):
    """This class supported two additional option attributes

    :ivar args: Whether this option need arguments. Must be one of
    'optional', 'required', 'no'. Defaults to 'optional'
    :ivar supported_cmds: For non-command options this should contain a
    tuple of all comman options, for which this option has a meaning. If
    this attribute is not set, the option is assumed to be valid for all
    commands"""
    ATTRS = Option.ATTRS + ['args', 'supported_cmds']

    def __init__(self, *opts, **attrs):
        Option.__init__(self, *opts, **attrs)

    def _check_attrs(self):
        if self.args is None:
            self.args = 'optional'
        if not self.args in ('optional', 'required', 'no'):
            raise OptionError("args must be on of: 'optional', 'required', "
                              "'no'", self)

    CHECK_METHODS = Option.CHECK_METHODS + [_check_attrs]


make_option = CommandOption


def _cb_cmd_opt(option, opt_str, value, parser):
    """OptionParser callback, which handles command options"""
    if hasattr(parser.values, 'command'):
        # raise error if two exlusive commands appeared
        msg = _('Please specify only one command option')
        raise OptionValueError(msg)
    parser.values.command = opt_str
    parser.values.command_values = value
    parser.values.args = option.args


class ConsoleIFace:
    """Provides a console interface to Tel"""

    # a simple pattern for phone numbers
    phone_number_pattern = re.compile(r'[-()/\d\s\W]+')
    # a simple pattern for mail addresses
    mail_pattern = re.compile(r'[^@\s]+@[^@\s]+\.[\w]+')

    def __init__(self):
        self.phonebook = None

    # INTERACTION FUNCTIONS

    def print_short_list(self, entries):
        """Prints all `entries` in a short format:
        If `entries` is None, all entries are printed"""
        print
        for entry in entries:
            print repr(entry)

    def print_long_list(self, entries):
        """Prints every single entry in `entries` in full detail.
        If `entries` is None, all entries are printed"""
        for entry in entries:
            print '-'*20
            print entry

    def print_table(self, entries):
        """Prints `entries` as a table. If `entries` is None, all entries
        are printed"""
        print
        # this is the head line of the table
        headline = (_('Index'), _('First name'), _('Last name'),
                    _('Street'), _('Postal code'), _('Town'), _('Mobile'),
                    _('Phone'), _('eMail'), _('Date of birth'))
        table_body = []
        # widths for each column
        column_widths = map(len, headline)
        for entry in entries:
            # create and add a row for each entry
            row = [str(entry.index), entry.firstname, entry.lastname,
                   entry.street, entry.postcode, entry.town, entry.mobile,
                   entry.phone, entry.email, entry.birthdate]
            table_body.append(row)
            # correct the column width, if an entry is too width
            column_widths = map(max, map(len, row), column_widths)
        # print the headline
        headline = map(str.center, headline, column_widths)
        headline = ' | '.join(headline)
        separator = map(lambda width: '-' * (width+2), column_widths)
        separator = '|'.join(separator)
        # this adds two spaces add begin and and of the row
        print '', headline, ''
        print separator
        for row in table_body:
            # format and print every row
            row[0] = row[0].rjust(column_widths[0])
            row[1:] = map(str.ljust, row[1:], column_widths[1:])
            row = ' | '.join(row)
            print '', row, ''

    def edit_entry(self, entry=None):
        """Allows interactive editing of entries. If `entry` is None, a new
        entry is created."""
        print
        if entry is None:
            new = True
            entry = Entry()
            print _('Creating a new entry...\n'
                    'Please fill the following fields. To leave a field '
                    'empty, just press ENTER without entering something.')
        else:
            new = False
            print _('Editing entry %s...\n'
                    'Please fill the following fields. To leave a field '
                    'unchanged, just press ENTER without entering '
                    'something.') % repr(entry)
        resp = raw_input(_('First name: ')).strip()
        if not new and not resp:
            # preserve old value, if entry is not new and we got no response
            resp = entry.firstname
        entry.firstname = resp
        resp = raw_input(_('Last name: ')).strip()
        if not new and not resp:
            resp = entry.lastname
        entry.lastname = resp
        resp = raw_input(_('Street and street number: ')).strip()
        if not new and not resp:
            resp = entry.street
        entry.street = resp
        while True:
            resp = raw_input(_('Postal code: ')).strip()
            try:
                # only verify, if something was entered
                if resp:
                    int(resp)
                elif not (resp and new):
                    resp = entry.postcode
                entry.postcode = resp
                break
            except ValueError:
                print _('You entered an invalid postal code. '
                        'Please retry ...')
        resp = raw_input(_('Town: ')).strip()
        if not new and not resp:
            resp = entry.town
        entry.town = resp
        while True:
            resp = raw_input(_('Mobile: ')).strip()
            if resp and not self.phone_number_pattern.match(resp):
                print _('You entered an invalid phone number')
                continue
            if not new and not resp:
                resp = entry.mobile
            entry.mobile = resp
            break
        while True:
            resp = raw_input(_('Phone: ')).strip()
            if resp and not self.phone_number_pattern.match(resp):
                print _('You entered an invalid mobile number')
                continue
            if not new and not resp:
                resp = entry.phone
            entry.phone = resp
            break              
        while True:
            resp = raw_input(_('eMail: ')).strip()
            if resp and not self.mail_pattern.match(resp):
                print _('You entered an invalid mail address')
                continue
            if not new and not resp:
                resp = entry.email
            entry.email = resp
            break
        resp = raw_input(_('Date of birth: ')).strip()
        if not new and not resp:
            resp = entry.birthdate
        entry.birthdate = resp
        print _('Thanks. The entry is now saved ...')
        self.phonebook.add(entry)
        self.phonebook.save()    

    # UTILITIES

    def parse_indices(self, *args):
        """Takes strings arguments, interprets them as numeric indices an
        returns a list of all entries denoted by these indices.

        The syntax looks like the following: 4-5 4 6 7

        Eachentry is only returned once, even if the index appears more than
        once
        :raises ValueError: If some string could not be interpreted"""
        entries = []
        try:
            for arg in args:
                if '-' in arg:
                    parts = arg.split('-')
                    for i in xrange(int(parts[0]), int(parts[1]) + 1):
                        try:
                            if self.phonebook[i] not in entries:
                                entries.append(self.phonebook[i])
                        except KeyError:
                            pass  # silently drop non exisiting keys
                else:
                    try:
                        entry = self.phonebook[int(arg)]
                        if entry not in entries:
                            entries.append(entry)
                    except KeyError:
                        pass  # silently drop non exisiting keys
            return entries
        except ValueError:
            sys.exit(_('Error: An invalid index was specified'))

    ## COMMAND FUNCTIONS

    # To add new commands to the interface, you need to do a few things.
    # This is the way you add the command --foo to the interface
    #
    # - Create a new method for the command. This method has the prefix
    #   _cmd_ and takes two arguments: options, which holds all options,
    #   that where given on the command line, and *args, which are all
    #   arguments specified on the command line:
    #
    #       def _cmd_foo(self, options, *args)
    #
    # - Add the option --foo to the command_options list.
    #   If --foo requires arguments, set the keyword argument 'args' to
    #   'required'. If it must not have any arguments, set it to 'no'.
    #   The default is 'optional'

    def _cmd_export(self, options, *args):
        """Exports phone book"""
        for path in args:
            if os.path.isfile(path):
                msg = _('%s already exists. Overwrite it? ')
                resp = raw_input(msg % path)
                if resp.lower() != 'y':
                    continue
            shutil.copyfile(self.phonebook.path, path)

    def _cmd_import(self, options, *args):
        """Import phone books"""
        for path in args:
            # import all specified phone books
            if os.path.exists(path):
                import_book = PhoneBook(path)
                for entry in import_book:
                    # enable auto-generation of index
                    entry.index = None
                    self.phonebook.add(entry)
        self.phonebook.save()

    def _cmd_table(self, options, *args):
        """Print a table"""
        if args:
            entries = self.parse_indices(*args)
        else:
            entries = self.phonebook
        self.print_table(entries)

    def _cmd_list(self, options, *args):
        """Print a list"""
        if args:
            entries = self.parse_indices(*args)
        else:
            entries = self.phonebook
        self.print_short_list(entries)

    def _cmd_show(self, options, *args):
        """Show a single entry"""
        if args:
            entries = self.parse_indices(*args)            
        else:
            entries = self.phonebook
        self.print_long_list(entries)

    def _cmd_search(self, options, *args):
        """Search the phone book for `pattern`"""
        found = []
        for pattern in args:
            entries = self.phonebook.search(pattern)
            # add all entries which aren't already in found. This avoids
            # printing entries twice, which are matched by more than one
            # pattern
            new = filter(lambda entry: entry not in found, entries)
            found += new
        self.print_table(found)

    def _cmd_create(self, options, *args):
        """Interactivly create a new entry"""
        number = 1
        if len(args) == 1:
            try:
                number = int(args[0])
            except ValueError:
                sys._exit(_('--create needs a number'))
        if len(args) > 1:
            sys.exit(_('--create accepts only one argument'))
        for func in itertools.repeat(self.edit_entry, 2):
            func()

    def _cmd_edit(self, options, *args):
        """Interactivly edit entries"""
        entries = self.parse_indices(*args)
        for entry in entries:
            self.edit_entry(entry)

    def _cmd_remove(self, options, *args):
        for entry in self.parse_indices(*args):
            resp = raw_input(_('Really delete entry %s? ') % repr(entry))
            if resp.lower() == 'y':
                self.phonebook.remove(entry)
        self.phonebook.save()
        
    ## COMMAND SUPPORT FUNCTIONS

    def _get_cmd_function(self, arg):
        """Returns the function for `arg`"""
        if arg.startswith('--'):
            # strip of the first to shlashes
            name = '_cmd_%s' % arg[2:]
        # and replace remaining slashes with underscores
        name = name.replace('-', '_')
        function = getattr(self, name)
        return function

    # OPTION PARSING

    usage = '%prog [--help|--version] [global options] command [arguments]'
             
    description = _('Tel is a little address book program for your '
                    'terminal')

    defaults = {
        'file': DEF_FILENAME
        }

    global_options = [
        make_option('-f', '--file', action='store', dest='file',
                    metavar=_('file'), help=_('Use FILE as phone book'))]

    command_options = [
        # command options
        make_option('--list', action='callback', callback=_cb_cmd_opt,
                    help=_('Print a short list of entries. Accepts a list '
                           'of indices')),
        make_option('--table', action='callback', callback=_cb_cmd_opt,
                    help=_('Prints a tables with entries. Accepts a list '
                           'of indices')),
        make_option('--show', action='callback', callback=_cb_cmd_opt,
                    help=_('Shows the specified entries.')),
        make_option('--search', action='callback', args='required',
                    help=_('Searches the phonebook for the specified '
                           'patterns'), callback=_cb_cmd_opt),
        make_option('--create', action='callback', callback=_cb_cmd_opt,
                    help=_('Creates the specified number of new entries')),
        make_option('--edit', action='callback', callback=_cb_cmd_opt,
                    help=_('Edits the entries at the specified indices'),
                    args='required'),
        make_option('--remove', action='callback', args='required',
                    help=_('Remove the entries at the specified indices'),
                    callback=_cb_cmd_opt),
        make_option('--export', action='callback', args='required',
                    help=_('Export phone book to all specified locations'),
                    callback=_cb_cmd_opt),
        make_option('--import', action='callback', args='required',
                    help=_('Import all specified phone books'),
                    callback=_cb_cmd_opt)
        ]

    local_options = []

    def _parse_args(self):
        """Parses command line arguments"""
        parser = OptionParser(usage=self.usage,
                              description=self.description,
                              version=__version__,
                              option_class=CommandOption,
                              conflict_handler='resolve')
        # command options
        desc = _('Commands to modify the phone book and to search or print '
                 'entries. Only one of these options may be specified. '
                 'Commands, which accept indices, recognize range '
                 'specifications like 4-6.')
        group = parser.add_option_group(_('Commands'), desc)
        group.add_options(self.command_options)
        # global options
        desc = _('These options are valid for every command')
        group = parser.add_option_group(_('Global options'), desc)
        group.add_options(self.global_options)


        parser.set_defaults(**self.defaults)
        (options, args) = parser.parse_args()
        
        if options.args == 'required' and not args:
            msg = _('The command %s need arguments')
            parser.error(msg % options.command)
        elif options.args == 'no' and args:
            msg = _('The command %s doesn\'t take any arguments')
            parser.error(msg % options.command)
        
        # get the command function
        options.command_function = self._get_cmd_function(options.command)
        
        return (options, args)

    def start(self):
        """Starts the interface"""
        try:
            (options, args) = self._parse_args()
            self.phonebook = PhoneBook(options.file)
            options.command_function(options, *args)
        except KeyboardInterrupt:
            sys.exit(_('Dying peacefully ...'))
    

if __name__ == '__main__':
    ConsoleIFace().start()

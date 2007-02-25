#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """\
Copyright (c) 2007 Sebastian Wiesner

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the \"Software\"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE."""

__version__ = '0.1.5-pre1'

__authors__ = ['Sebastian Wiesner <basti.wiesner@gmx.net>']

import os
import sys
import csv
import itertools
import shutil
import re
import textwrap
import gettext
_ = gettext.gettext

try:
    # more comfortable line editing
    import readline
except ImportError:
    pass

from copy import copy
from optparse import (Option, OptionError, OptionParser, OptionValueError,
                      IndentedHelpFormatter)


# The directory, where tel stores its config
CONFIG_DIR = os.path.expanduser(os.path.join('~', '.tel'))
if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)
# the default phonebook
DEF_FILENAME = os.path.join(CONFIG_DIR, 'phonebook.csv')

# PHONEBOOK CLASSES

class Entry(object):
    """This class stores a single adress entry.

    :cvar translations: Maps fieldnames to user-readable translations
    :cvar default_order: A list of all field names in the default order in
    which they should be saved or printed
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
    :ivar tags: The famous web 2.0 thingy
    """

    # mainly important for table printing and field specifications
    translations = {
        'index': _('Index'),
        'firstname': _('First name'),
        'lastname': _('Last name'),
        'street': _('Street and number'),
        'postcode': _('Postal code'),
        'town': _('Town'),
        'mobile': _('Mobile'),
        'phone': _('Phone'),
        'email': _('eMail'),
        'birthdate': _('Date of birth'),
        'tags': _('Tags')
        }

    default_order = ['index', 'firstname', 'lastname', 'street', 'postcode',
                     'town', 'mobile', 'phone', 'email', 'birthdate', 'tags']

    # FIXME: convert attributes into properties to support type checking
    # FIXME: we could use new style classes here
                  
    def __init__(self):
        # init all fields
        self.index = None
        self.firstname = ''
        self.lastname = ''
        self.street = ''
        self.postcode = ''
        self.town = ''
        self.mobile = ''
        self.phone = ''
        self.email = ''
        self.birthdate = ''
        self.tags = ''

    def __str__(self):
        # return a pretty representation
        # NOTE: this doesn't respect field translations to allow pretty
        # printing without being bound to field limits
        # TODO: use textwrap here to prevent overlong lines
        msg = _('Index:          %(index)s\n'
                'Name:           %(firstname)s %(lastname)s\n'
                'Street:         %(street)s\n'
                'Town:           %(postcode)s %(town)s\n'
                'Phone:          %(phone)s\n'
                'Mobile:         %(mobile)s\n'
                'eMail:          %(email)s\n'
                'Date of birth:  %(birthdate)s\n'
                'Tags:           %(tags)\n') % self.__dict__
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
        for field in self.default_order:
            if getattr(self, field) != getattr(other, field):
                return True
        return False

    def __eq__(self, other):
        return not self.__ne__(other)

    def __hash__(self):
        hash_ = 0
        for field in self.default_order:
            hash_ ^= hash(getattr(self, field))
        return hash_

    def __repr__(self):
        # return a short representation
        return _('[%(index)s] %(firstname)s %(lastname)s') % self.__dict__

    def __nonzero__(self):
        # whether the entry is empty. an empty entry is an entry whose
        # fields (except index) are empty.  Since index is auto-created on
        # most cases, an empty entry can have an index.
        for field in self.default_order:
            if field != 'index' and getattr(self, field):
                return True
        return False

    def matches(self, pattern, ignore_case=False, regexp=False,
                fields=None):
        """Note, that this method does *not* support regular expressions.
        :param pattern: A string pattern, which is searched in this entry
        :param regexp: Whether pattern is a regular expression or not
        :param fields: the fields to search in
        :returns: True, if any field in this entry matches `pattern`,
        False otherwise"""
        if fields is None:
            fields = self.default_order
        for field in fields:
            if regexp:
                flags = re.UNICODE | re.LOCALE
                if ignore_case:
                    flags = flags | re.IGNORECASE
                if bool(re.search(pattern, str(getattr(self, field)),
                                  flags)):
                    return True
            else:
                value = str(getattr(self, field))
                if ignore_case:
                    pattern = pattern.lower()
                    value = value.lower()
                # very simple searching algo ;)
                if pattern in value:
                    return True
        return False


class PhoneBook:
    """This class provides an interface to the phone book

    :ivar path: The file, from which this Phonebook was loaded.
    """

    def __init__(self, path):
        """Creates a PhoneBook from the file denoted by `path`"""
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
            if value.index is not None:
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
        fields = Entry.default_order
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

    def search(self, *args, **kwargs):
        """Searchs the phone book.
        `*args` and `**kwargs` are the same as for Entry.matches"""
        found_entries = []
        for entry in self:
            if entry.matches(*args, **kwargs):
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

# EXTENDING OptionParser

class CommandHelpFormatter(IndentedHelpFormatter):
    """A Formatter, which respects certain command properties
    like args"""

    def format_option(self, option):
        """Extend option formatting to include formatting of supported
        options."""
        result = IndentedHelpFormatter.format_option(self, option)
        if option.command and option.options:
            result = [result]
            options = ', '.join(option.options)
            msg = _('Supported options: ')
            # build the complete options string and wrap it to width of the
            # help
            opt_str = ''.join([msg, options])
            lines = textwrap.wrap(opt_str, self.help_width - 4)
            # this is the first line, which includes the message
            first_line = lines[0]
            first_indent = self.help_position + 4
            # reindent and wrap the remaining option lines
            opt_str = ' '.join(lines[1:])
            options_indent = first_indent + len(msg)
            lines = textwrap.wrap(opt_str, self.help_width - len(msg))

            result.append('%*s%s\n' % (first_indent, '', first_line))
            result.extend(['%*s%s\n' % (options_indent, '', line) for line
                           in lines])
            result = ''.join(result)
        return result
        
    
    def format_option_strings(self, option):
        """Extend option string formatting to support arguments for
        commands"""
        if option.command and not option.args == 'no':
            arg_name = option.metavar or 'indices'
            if option.args == 'optional':
                arg_name = ''.join(['[', arg_name, ']'])
            lopts = [' '.join([lopt, arg_name]) for lopt in
                     option._long_opts]
            return ', '.join(lopts)
        else:
            return IndentedHelpFormatter.format_option_strings(self, option)
    

class CommandOption(Option):
    """This class supported two additional option attributes

    :ivar args: Whether this option need arguments. Must be one of
    'optional', 'required', 'no'. Defaults to 'optional'
    :ivar options: A list of all options, this command supports. Only used
    for help formatting.
    :command: whether this option is a command. Important for help
    formatting"""
    ATTRS = Option.ATTRS + ['args', 'options']
    TYPES = Option.TYPES + ('field_list',)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)

    def _check_command(self):
        # command options can be identified by checking the callback
        # keyword
        self.command = self.callback == cb_cmd_opt

    def _check_attrs(self):
        if self.args is None:
            self.args = 'optional'
        if not self.args in ('optional', 'required', 'no'):
            raise OptionError("args must be on of: 'optional', 'required', "
                              "'no'", self)

    def _check_options(self):
        if self.options and not isinstance(self.options, (tuple, list)):
            raise OptionError('options must be a tuple or a list', self)

    def _check_field_list(self, opt, value):
        """Parse field_list options into a list of fields"""
        warning_msg = _('WARNING: There is no field %s')
        items = map(str.strip, value.split(','))
        # filter empty fields
        # (which came from something like "index,,firstname")
        items = filter(None, items)
        fields_to_show = []
        fields_to_hide = []
        for item in items:
            name = item.lstrip('-')
            if name not in Entry.default_order:
                print >> sys.stderr, warning_msg % name
                continue
            if item.startswith('-'):
                fields_to_hide.append(name)
            else:
                fields_to_show.append(name)
        if not fields_to_show:
            fields_to_show = Entry.default_order[:]
        for field in fields_to_hide:
            if field in fields_to_show:
                fields_to_show.remove(field)
        return fields_to_show
            
    CHECK_METHODS = Option.CHECK_METHODS + [_check_attrs, _check_command,
                                            _check_options]
    TYPE_CHECKER['field_list'] = _check_field_list
    

make_option = CommandOption

# OPTION CALLBACKS

def cb_print_license(*args, **kwargs):
    """Print license information"""
    print __license__
    sys.exit()

def cb_print_copyright(*args, **kwargs):
    """Print copyright information"""
    print __license__.splitlines()[0]
    sys.exit()

def cb_print_authors(*args, **kwargs):
    """Print author information"""
    print '\n'.join(__authors__)
    sys.exit()

def cb_print_fields(*args, **kwargs):
    """Print fields"""
    items = [(Entry.translations[field], field) for field in
             Entry.default_order]
    headline = [_('Field'), _('Internal name')]
    column_widths = map(len, headline)
    for item in items:
        column_widths = map(max, map(len, item), column_widths)
    headline = ' - '.join(map(str.center, headline, column_widths))
    separator = '-' * (column_widths[0] + column_widths[1] + 5)
    print ' ', headline
    print '', separator
    for item in items:
        item = ' - '.join(map(str.ljust, item, column_widths))
        print ' ', item
    sys.exit()

def cb_cmd_opt(option, opt_str, value, parser):
    """OptionParser callback, which handles command options"""
    if hasattr(parser.values, 'command'):
        # raise error if two exlusive commands appeared
        msg = _('Please specify only one command option')
        raise OptionValueError(msg)
    parser.values.command = opt_str
    parser.values.command_values = value
    parser.values.args = option.args


class ConsoleEntryEditor:
    """This class provides a simple console-based entry editor.

    :ivar current_field: The name of the currently edited field"""

    # a simple pattern for phone numbers
    phone_number_pattern = re.compile(r'[-()/\d\s\W]+')
    # a simple pattern for mail addresses
    mail_pattern = re.compile(r'[^@\s]+@[^@\s]+\.[\w]+')

    # this is a list of all editable fields
    # each item is a tuple containing the following values:
    #  'fieldname' as used by the Entry class
    #  'error_message' when verification failed
    fields = [
        ('firstname', None),
        ('lastname', None),
        ('street', None),
        ('postcode', _('You entered an invalid postal code!')),
        ('town', None),
        ('mobile', _('You entered an invalid mobile number!')),
        ('phone', _('You entered an invalid phone number!')),
        ('email', _('You entered an invalid eMail address!')),
        ('birthdate', None),
        ('tags', None)]

    edit_msg = _('Editing entry %r...')
    new_msg = _('Creating a new entry...')
         
    def verify_phone_number(self, number):
        return bool(self.phone_number_pattern.match(number))

    def verify_mail_address(self, address):
        return bool(self.mail_pattern.match(address))

    def verify_postal_code(self, code):
        try:
            int(code)
            return True
        except ValueError:
            return False

    def verify_field(self, field, value):
        """Verifies input"""
        # don't check empty fields
        if not value:
            return True
        if field == 'email':
            return self.verify_mail_address(value)
        elif field in ('mobile', 'phone'):
            return self.verify_phone_number(value)
        elif field == 'postcode':
            return self.verify_postal_code(value)
        else:
            return True
        
    try:
        # force raising a NameError if readline isn't present
        readline
        
        def _input_hook(self):
            """displays the current value in the input line"""
            if self.edited_entry:
                val = getattr(self.edited_entry, self.current_field)
                readline.insert_text(val)
                readline.redisplay()
        
        # an edit method with readline support
        def edit(self, entry=None):
            """Edits the specified `entry`. If `entry` is None, a new entry
            is created. This method supports the readline module for editing

            :returns: The entry with the new values as entered by the
            user"""
            if entry is None:
                entry = Entry()
                print self.new_msg
                help = _('Please fill the following fields. To leave a '
                         'field empty, just press ENTER without entering '
                         'something.')
                print textwrap.fill(help)
            else:
                self.edited_entry = entry
                print self.edit_msg % entry
                help = _('Please fill the following fields.')
                print textwrap.fill(help)
                # set input hook to show the current value
                readline.set_pre_input_hook(self._input_hook)
            print
            for field in self.fields:
                self.current_field = field[0]
                prompt = '%s: ' % Entry.translations[field[0]]
                resp = raw_input(prompt).strip()
                while not self.verify_field(field[0], resp):
                    print field[1]
                    resp = raw_input(prompt).strip()
                setattr(entry, field[0], resp)
            # remove input hook
            readline.set_pre_input_hook(None)
            return entry
        
    except NameError:
        # the non-readline version
        def edit(self, entry=None):
            """Edits the specified `entry`. If `entry` is None, a new entry
            is created.

            :returns: The entry with the new values as entered by the
            user"""
            if entry is None:
                entry = Entry()
                print self.new_msg
                help = _('Please fill the following fields. To leave a '
                         'field empty, just press ENTER without entering '
                         'something.')
                print textwrap.fill(help, 79)
            else:
                print self.edit_msg % entry
                help = _('Please fill the following fields. The current '
                         'value is shown in square brackets. NOTE: The '
                         'current value is not preserved. You have to '
                         're-enter every value!')
                print textwrap.fill(help, 79)
            print
            for field in self.fields:
                self.current_field = field[0]
                prompt = '%s: [%s] ' % (Entry.translations[field[0]],
                                        getattr(entry, field[0]))
                resp = raw_input(prompt).strip()
                while not self.verify_field(field[0], resp):
                    print field[1]
                    resp = raw_input(prompt).strip()
                setattr(entry, field[0], resp)
            return entry
            

class ConsoleIFace:
    """Provides a console interface to Tel"""

    def __init__(self):
        self.phonebook = None

    # INTERACTION FUNCTIONS

    def print_short_list(self, entries):
        """Prints all `entries` in a short format:"""
        print
        for entry in entries:
            print repr(entry)

    def print_long_list(self, entries):
        """Prints every single entry in `entries` in full detail."""
        for entry in entries:
            print '-'*20
            print entry

    def print_table(self, entries, fields):
        """Prints `entries` as a table."""
        print
        # this is the head line of the table
        headline = map(Entry.translations.get, fields)
        table_body = []
        # widths for each column
        column_widths = map(len, headline)
        for entry in entries:
            # create and add a row for each entry
            row = [str(getattr(entry, field)) for field in fields]
            table_body.append(row)
            # correct the column width, if an entry is too width
            column_widths = map(max, map(len, row), column_widths)
        # print the headline
        headline = map(str.center, headline, column_widths)
        headline = '| %s |' % ' | '.join(headline)
        separator = map(lambda width: '-' * (width+2), column_widths)
        separator = '|%s|' % '|'.join(separator)
        # this adds two spaces add begin and and of the row
        print headline
        print separator
        for row in table_body:
            # FIXME: index should be right-justified
            row = map(str.ljust, row, column_widths)
            row = '| %s |' % ' | '.join(row)
            print row

    def edit_entry(self, entry=None):
        """Allows interactive editing of entries. If `entry` is None, a new
        entry is created."""
        print
        editor = ConsoleEntryEditor()
        entry = editor.edit(entry)
        # check if the user wants to add an empty entry
        if not entry:
            msg = _('Do you really want to save an emtpy entry? ')
            resp = raw_input(msg)
            if resp != 'y':
                # abort without saving
                print _('The entry is not saved')
                return
        self.phonebook.add(entry)
        self.phonebook.save()
        print 'The entry was saved'

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
    #   The default is 'optional'. Command options *must* always invoke the
    #   callback cb_cmd_opt! 
    # - If --foo should support options, add the options to the
    #   local_options list. To make these options appear along with the
    #   command help, add the keyword argument "options" to the command
    #   option and provide it with a list or tuple of supported options.
    #   These options can be queried trough the options argument of the
    #   command function

    def _cmd_export(self, options, *args):
        """Exports phone book"""
        for path in args:
            if not os.path.exists(path) and not os.path.basename(path):
                # create non-existing directories here, if the user wants it
                msg = _('Directory %s does not exist. Create it? ')
                resp = raw_input(msg % path)
                if resp.lower() == 'y':
                    os.makedirs(path)
                else:
                    # do not export
                    continue
            if os.path.isdir(path):
                # if path is a directory, create the export target by
                # joining the filename of the phone book with the path
                filename = os.path.basename(self.phonebook.path)
                path = os.path.join(path, filename)
            if os.path.isfile(path):
                # now check, if the file denoted by path already exists
                msg = _('%s already exists. Overwrite it? ')
                resp = raw_input(msg % path)
                if resp.lower() != 'y':
                    continue
            try:
                shutil.copyfile(self.phonebook.path, path)
            except IOError, e:
                if e.errno == 13:
                    msg = _('ERROR: Permission denied for %s') % path
                else:
                    msg = e
                print >> sys.stderr, msg

    def _cmd_import(self, options, *args):
        """Import phone books"""
        for path in args:
            # import all specified phone books
            if os.path.exists(path):
                if (os.path.abspath(path) ==
                    os.path.abspath(self.phonebook.path)):
                    resp = raw_input(_('Do you really want to import the '
                                       'phone book you\'re just using? '))
                    if resp.lower() != 'y':
                        print _('Not importing %s...') % path
                        continue
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
        self.print_table(entries, options.output)

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
            entries = self.phonebook.search(pattern, options.ignore_case,
                                            options.regexp, options.fields)
            # add all entries which aren't already in found. This avoids
            # printing entries twice, which are matched by more than one
            # pattern
            new = filter(lambda entry: entry not in found, entries)
            found += new
        self.print_table(found, options.output)

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
        for func in itertools.repeat(self.edit_entry, number):
            func()

    def _cmd_edit(self, options, *args):
        """Interactivly edit entries"""
        entries = self.parse_indices(*args)
        for entry in entries:
            self.edit_entry(entry)

    def _cmd_remove(self, options, *args):
        for entry in self.parse_indices(*args):
            resp = raw_input(_('Really delete entry "%s"? ') % repr(entry))
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

    usage = '%prog [global options] command [arguments]'
             
    description = _('Tel is a little address book program for your '
                    'terminal.')

    defaults = {
        'file': DEF_FILENAME,
        'output': Entry.default_order,
        'ignore_case': False
        }

    parser_options = [
        make_option('--license', action='callback',
                    callback=cb_print_license,
                    help=_('show license information and exit')),
        make_option('--copyright', action='callback',
                    callback=cb_print_copyright,
                    help=_('show copyright information and exit')),
        make_option('--authors', action='callback',
                    callback=cb_print_authors,
                    help=_('show author information and exit')),
        make_option('--help-fields', action='callback',
                    callback=cb_print_fields,
                    help=_('print a list of all fields and exit. The '
                           'internal name as printed by this options must '
                           'be used, when specifying fields on command '
                           'line.'))]

    global_options = [
        make_option('-f', '--file', action='store', dest='file',
                    metavar=_('file'), help=_('use FILE as phone book'))]

    command_options = [
        # command options
        make_option('--list', action='callback', callback=cb_cmd_opt,
                    help=_('print a short list of the specified entries')),
        make_option('--table', action='callback', callback=cb_cmd_opt,
                    help=_('prints a table with the specified entries.'),
                    options=['--output']),
        make_option('--show', action='callback', callback=cb_cmd_opt,
                    help=_('shows the specified entries.')),
        make_option('--search', action='callback', args='required',
                    help=_('searches the phonebook for the specified '
                           'patterns'), callback=cb_cmd_opt,
                    metavar='patterns',
                    options=['--regexp, --output', '--fields',
                             '--ignore-case']),
        make_option('--create', action='callback', callback=cb_cmd_opt,
                    help=_('creates the specified number of new entries'),
                    metavar='number'),
        make_option('--edit', action='callback', callback=cb_cmd_opt,
                    help=_('edits the entries at the specified indices'),
                    args='required'),
        make_option('--remove', action='callback', args='required',
                    help=_('remove the entries at the specified indices'),
                    callback=cb_cmd_opt),
        make_option('--export', action='callback', args='required',
                    help=_('export phone book to all specified locations'),
                    callback=cb_cmd_opt, metavar='targets'),
        make_option('--import', action='callback', args='required',
                    help=_('import all specified phone books'),
                    callback=cb_cmd_opt, metavar='files')]

    local_options = [
        make_option('-r', '--regexp', action='store_true', dest='regexp',
                    help=_('enable regular expressions. tel uses the '
                           'Python-syntax. You can find an overview at the '
                           'following URL: '
                           'http://docs.python.org/lib/re-syntax.html')),
        make_option('-o', '--output', action='store', dest='output',
                    type='field_list', metavar='FIELDS', 
                    help=_('specifies the fields to show. Takes a '
                           'comma-separated list of internal names as '
                           'printed by --help-fields. Fields prefixed '
                           'with "-" are hidden.')),
        make_option('-i', '--ignore-case', action='store_true',
                    dest='ignore_case',
                    help=_('ignore case, when searching. The default is '
                           'not to ignore case.')),
        # FIXME: someone knows a good short options for --fields?
        make_option('--fields', action='store', dest='fields',
                    type='field_list',
                    help=_('Specifies a list of fields to search in. '
                    'Accepts the same syntax as the --output option'))]

    def _parse_args(self):
        """Parses command line arguments"""
        parser = OptionParser(prog='tel',
                              usage=self.usage,
                              description=self.description,
                              version=__version__,
                              option_class=CommandOption,
                              option_list=self.parser_options,
                              formatter=CommandHelpFormatter())
        # command options
        desc = _('Commands to modify the phone book and to search or print '
                 'entries. Only one of these options may be specified. '
                 'Commands, which accept indices, recognize range '
                 'specifications like 4-6.')
        group = parser.add_option_group(_('Commands'), desc)
        group.add_options(self.command_options)
        # global options
        desc = _('These options are valid with every command')
        group = parser.add_option_group(_('Global options'), desc)
        group.add_options(self.global_options)
        desc = _('These options are only supported by certain commands. If '
                 'you use them with other commands, they are just ignored.')
        group = parser.add_option_group(_('Special options'), desc)
        group.add_options(self.local_options)
            
        parser.set_defaults(**self.defaults)
        (options, args) = parser.parse_args()

        if not hasattr(options, 'command'):
            parser.error(_('Please specify a command'))
        
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

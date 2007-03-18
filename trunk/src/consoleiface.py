#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import sys
import itertools
import shutil
import re
import textwrap
import gettext

try:
    # more comfortable line editing
    import readline
except ImportError:
    pass

# tel modules
import tel
import phonebook
from cmdoptparse import CommandOptionParser, make_option


_ = gettext.translation('tel', tel.CONFIG.MESSAGES).ugettext


# The directory, where tel stores its config
CONFIG_DIR = os.path.expanduser(os.path.join('~', '.tel'))
if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)
# the default phonebook
DEF_FILENAME = os.path.join(CONFIG_DIR, 'phonebook.csv')


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
                entry = phonebook.Entry()
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
                prompt = '%s: ' % phonebook._TRANSLATIONS[field[0]]
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
                new = True
                entry = phonebook.Entry()
                print self.new_msg
                help = _('Please fill the following fields. To leave a '
                         'field empty, just press ENTER without entering '
                         'something.')
                print textwrap.fill(help, 79)
            else:
                new = False
                print self.edit_msg % entry
                help = _('Please fill the following fields. The current '
                         'value is shown in square brackets. NOTE: The '
                         'current value is not preserved. You have to '
                         're-enter every value!')
                print textwrap.fill(help, 79)
            print
            for field in self.fields:
                self.current_field = field[0]
                if new:
                    prompt = '%s: ' % phonebook._TRANSLATIONS[field[0]]
                else:
                    prompt = '%s [%s]: '
                    prompt % (phonebook._TRANSLATIONS[field[0]],
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

    def print_short_list(self, entries, sortby='index', desc=False):
        """Prints all `entries` in a short format.
        :param sortby: The field to sort by
        :param asc: True, if sorting order is descending"""
        entries = phonebook.sort_entries_by_field(entries, sortby, desc)
        print
        for entry in entries:
            print repr(entry)

    def print_long_list(self, entries, sortby='index', desc=False):
        """Prints every single entry in `entries` in full detail.
        :param sortby: The field to sort by
        :param asc: True, if sorting order is descending"""
        entries = phonebook.sort_entries_by_field(entries, sortby, desc)
        for entry in entries:
            print '-'*20
            print entry

    def print_table(self, entries, fields, sortby='index', desc=False):
        """Prints `entries` as a table.
        :param sortby: The field to sort by
        :param asc: True, if sorting order is descending"""
        entries = phonebook.sort_entries_by_field(entries, sortby, desc)
        print
        # this is the head line of the table
        headline = map(phonebook.translate_field, fields)
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
        once"""
        entries = []
        try:
            for arg in args:
                if '-' in arg:
                    start, end = map(int, arg.split('-'))
                    if not start in self.phonebook:
                        msg = _('WARNING: start index %s out of range')
                        print >> sys.stderr, msg % start
                    if not end in self.phonebook:
                        msg = _('WARNING: end index %s out of range')
                        print >> sys.stderr, msg % end
                    # verify start and end
                    # FIXME: use slicing here, if phone supports it
                    for i in xrange(start, end+1):
                        try:
                            # check if we have already added the index
                            if self.phonebook[i] not in entries:
                                entries.append(self.phonebook[i])
                        except KeyError:
                            # silenty ignore non-existing keys here
                            # this avoids page-long listings for typing
                            # mistakes like 5-100 instead of 5-10
                            pass 
                else:
                    index = int(arg)
                    try:
                        entry = self.phonebook[index]
                        # check if we have already added the index
                        if entry not in entries:
                            entries.append(entry)
                    except KeyError:
                        msg = _('WARNING: There is no entry with index %s')
                        print >> sys.stderr, msg % index
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
                    msg = _('Error: Permission denied for %s') % path
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
                import_book = phonebook.PhoneBook(path)
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
        self.print_table(entries, options.output, options.sortby[0],
                         options.sortby[1])

    def _cmd_list(self, options, *args):
        """Print a list"""
        if args:
            entries = self.parse_indices(*args)
        else:
            entries = self.phonebook
        self.print_short_list(entries, options.sortby[0], options.sortby[1])

    def _cmd_show(self, options, *args):
        """Show a single entry"""
        if args:
            entries = self.parse_indices(*args)            
        else:
            entries = self.phonebook
        self.print_long_list(entries, options.sortby[0], options.sortby[1])

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
        self.print_table(found, options.output, options.sortby[0],
                         options.sortby[1])

    def _cmd_create(self, options, *args):
        """Interactivly create a new entry"""
        number = 1
        if len(args) == 1:
            try:
                number = int(args[0])
            except ValueError:
                sys.exit(_('--create needs a number'))
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
        return getattr(self, '_cmd_'+arg)

    # OPTION PARSING

    usage = _('%prog [options] command [arguments]')

    description = _('tel is a little address book program for your '
                    'terminal.')

    defaults = {
        'file': DEF_FILENAME,
        'output': phonebook.FIELDS,
        'ignore_case': False,
        'sortby': ('index', False)
        }

    global_options = [
        make_option('-f', '--file', action='store', dest='file',
                    metavar=_('file'), help=_('use FILE as phone book'))]

    command_options = [
        # command options
        make_option('--list', action='command', options=['--sort-by'],
                    help=_('print a short list of the specified entries')),
        make_option('--table', action='command',
                    help=_('print a table with the specified entries.'),
                    options=['--output', '--sort-by']),
        make_option('--show', action='command', options=['--sort-by'],
                    help=_('show the specified entries')),
        make_option('--search', action='command', args='required',
                    help=_('search the phonebook for the specified '
                           'patterns'), metavar=_('patterns'),
                    options=['--regexp, --output', '--fields',
                             '--ignore-case', '--sort-by']),
        make_option('--create', action='command', metavar=_('number'),
                    help=_('create the specified number of new entries')),
        make_option('--edit', action='command', args='required',
                    help=_('edit the entries at the specified indices')),
        make_option('--remove', action='command', args='required',
                    help=_('remove the entries at the specified indices')),
        make_option('--export', action='command', args='required',
                    help=_('export phone book to all specified locations'),
                    metavar=_('targets')),
        make_option('--import', action='command', args='required',
                    help=_('import all specified phone books'),
                    metavar=_('files'))]

    local_options = [
        make_option('-r', '--regexp', action='store_true', dest='regexp',
                    help=_('enable regular expressions. tel uses the '
                           'Python-syntax. You can find an overview at the '
                           'following URL: '
                           'http://docs.python.org/lib/re-syntax.html')),
        make_option('-o', '--output', action='store', dest='output',
                    type='field_list', metavar=_('fields'), 
                    help=_('specify the fields to show. Takes a '
                           'comma-separated list of internal names as '
                           'printed by --help-fields. Fields prefixed '
                           'with "-" are hidden.')),
        make_option('-i', '--ignore-case', action='store_true',
                    dest='ignore_case',
                    help=_('ignore case, when searching. The default is '
                           'not to ignore case.')),
        # FIXME: someone knows a good short options for --fields?
        make_option('--fields', action='store', dest='fields',
                    type='field_list', metavar=_('fields'),
                    help=_('specify a list of fields to search in. '
                    'Accepts the same syntax as the --output option')),
        make_option('-s', '--sort-by', type='field', dest='sortby',
                    metavar=_('field'),
                    help=_('sort output. Specify a field name as printed '
                           'by --help-fields. If prefixed with +, sorting '
                           'order is ascending, if prefixed with a -, '
                           'sorting order is descending. The default is '
                           'ascending, if no prefix is used.'))]

    def _parse_args(self):
        """Parses command line arguments"""
        license = tel.__license__
        parser = CommandOptionParser(prog='tel',
                                     usage=self.usage,
                                     description=self.description,
                                     version=tel.__version__,
                                     authors=tel.__authors__,
                                     license=license,
                                     copyright=license.splitlines()[0])
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
            self.phonebook = phonebook.PhoneBook(options.file)
            options.command_function(options, *args)
        except KeyboardInterrupt:
            sys.exit(_('Dying peacefully ...'))

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


_TRANSLATION = gettext.translation('tel', tel.CONFIG.MESSAGES)
_STDOUT_ENCODING = sys.stdout.encoding or sys.getfilesystemencoding()
_STDIN_ENCODING = sys.stdin.encoding or sys.getfilesystemencoding()


def _(msg):
    return _TRANSLATION.ugettext(msg).encode(_STDOUT_ENCODING)


def entry_repr(entry):
    """Returns a short representation of `entry` in appropriate encoding for
    console output"""
    msg = _('[%(index)s] %(firstname)s %(lastname)s') % entry
    return msg.encode(_STDOUT_ENCODING)


class ConsoleEntryEditor:
    """This class provides a simple console-based entry editor.

    :ivar current_field: The name of the currently edited field"""

    EDIT_MSG = _('Editing entry "%s"...')
    NEW_MSG = _('Creating a new entry...')
         
    def edit(self, entry=None):
        """Edits `entry`. If `entry` is none, a new entry is created.
        This method supports readline, if available.
        :returns: The edited `entry`"""
        if entry is None:
            entry = phonebook.Entry()
            new = True
            print self.NEW_MSG
        else:
            new = False
            print self.EDIT_MSG % entry_repr(entry)

        self.initialize_editor(new)
        self.print_help(new)
        for field in phonebook.FIELDS[1:]:
            oldvalue = entry[field]
            while True:
                value = self.get_input(field, oldvalue, new)
                value = value.strip()
                value = value.decode(_STDIN_ENCODING)
                try:
                    entry[field] = value
                    break
                except ValueError:
                    msg = _('You entered an invalid value for the field'
                            '"%s"!')
                    print msg % phonebook.translate_field(field)
        self.finalize_editor()
        return entry

        
    try:
        # force raising a NameError if readline isn't present
        readline

        # input methods supporting readline
        def print_help(self, new):
            if new:
                help = _('Please fill the following fields. To leave a '
                         'field empty, just press ENTER without entering '
                         'something.')
                print textwrap.fill(help)
            else:
                print _('Please fill the following fields.')

        def initialize_editor(self, new):
            """Initialize the editor"""
            if not new:
                readline.set_pre_input_hook(self._input_hook)

        def finalize_editor(self):
            readline.set_pre_input_hook(None)

        def get_input(self, field, oldvalue, new):
            """Gets a value from command line input.

            :param field: The fieldname of the edited field
            :param oldvalue: The old value of the field
            :param new: Whether the entry is new"""
            if not new:
                self.oldvalue = oldvalue
            else:
                self.oldvalue = None
            prompt = '%s: ' % phonebook.translate_field(field)
            prompt = prompt.encode(_STDOUT_ENCODING)
            return raw_input(prompt)
            
        def _input_hook(self):
            """displays the current value in the input line"""
            if self.oldvalue:
                readline.insert_text(self.oldvalue.encode(_STDOUT_ENCODING))
                readline.redisplay()
        
    except NameError:

        # don't do anything
        def initialize_editor(*args, **kwargs):
            pass
        finalize_editor = initialize_editor
        
        def print_help(self, new):
            """Print a little editing help"""
            if new:
                help = _('Please fill the following fields. To leave a '
                         'field empty, just press ENTER without entering '
                         'something.')
                print textwrap.fill(help, 79)
            else:
                help = _('Please fill the following fields. The current '
                         'value is shown in square brackets. NOTE: The '
                         'current value is not preserved. You have to '
                         're-enter every value!')
                print textwrap.fill(help, 79)

        def get_input(self, field, oldvalue, new):
            """Gets a value from command line input.

            :param field: The fieldname of the edited field
            :param oldvalue: The old value of the field
            :param new: Whether the entry is new"""
            if new:
                prompt = '%s: ' % phonebook.translate_field(field)
            else:
                prompt = '%s [%s]: '
                prompt = prompt % (phonebook.translate_field(field),
                                   oldvalue)
            prompt = prompt.encode(_STDOUT_ENCODING)
            return raw_input(prompt)
            

class ConsoleIFace:
    """Provides a console interface to Tel"""

    def __init__(self):
        self.phonebook = None

    # INTERACTION FUNCTIONS

    def print_short_list(self, entries):
        """Prints all `entries` in a short format."""
        print
        for entry in entries:
            print entry_repr(entry)

    def print_long_list(self, entries, sortby='index', desc=False):
        """Prints every single entry in `entries` in full detail.
        :param sortby: The field to sort by
        :param asc: True, if sorting order is descending"""
        for entry in entries:
            print '-'*20
            print unicode(entry).encode(_STDOUT_ENCODING)

    def print_table(self, entries, fields):
        """Prints `entries` as a table.
        :param fields: Fields to include in the table"""
        print
        # this is the head line of the table
        headline = map(phonebook.translate_field, fields)
        table_body = []
        # widths for each column
        column_widths = map(len, headline)
        for entry in entries:
            # create and add a row for each entry
            row = [unicode(entry[field]) for field in fields]
            table_body.append(row)
            # correct the column width, if an entry is too width
            column_widths = map(max, map(len, row), column_widths)
        # print the headline
        headline = map(unicode.center, headline, column_widths)
        headline = '| %s |' % ' | '.join(headline)
        separator = map(lambda width: '-' * (width+2), column_widths)
        separator = '|%s|' % '|'.join(separator)
        # this adds two spaces add begin and and of the row
        print headline.encode(_STDOUT_ENCODING)
        print separator.encode(_STDOUT_ENCODING)
        for row in table_body:
            # FIXME: index should be right-justified
            row = map(unicode.ljust, row, column_widths)
            row = '| %s |' % ' | '.join(row)
            print row.encode(_STDOUT_ENCODING)

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
        entries = phonebook.sort_entries_by_field(entries,
                                                  options.sortby[0],
                                                  options.sortby[1],
                                                  options.ignore_case)
        self.print_table(entries, options.output)

    def _cmd_list(self, options, *args):
        """Print a list"""
        if args:
            entries = self.parse_indices(*args)
        else:
            entries = self.phonebook
        entries = phonebook.sort_entries_by_field(entries,
                                                  options.sortby[0],
                                                  options.sortby[1],
                                                  options.ignore_case)
        self.print_short_list(entries)

    def _cmd_show(self, options, *args):
        """Show a single entry"""
        if args:
            entries = self.parse_indices(*args)            
        else:
            entries = self.phonebook
        entries = phonebook.sort_entries_by_field(entries,
                                                  options.sortby[0],
                                                  options.sortby[1],
                                                  options.ignore_case)
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
        entries = phonebook.sort_entries_by_field(found,
                                                  options.sortby[0],
                                                  options.sortby[1],
                                                  options.ignore_case)
        self.print_table(found, options.output)

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
            resp = raw_input(_('Really delete entry "%s"? ') %
                             entry_repr(entry))
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
        'file': tel.CONFIG.DEF_FILENAME,
        'output': phonebook.FIELDS,
        'ignore_case': False,
        'sortby': ('index', False),
        'fields': phonebook.FIELDS
        }

    global_options = [
        make_option('-f', '--file', action='store', dest='file',
                    metavar=_('file'), help=_('use FILE as phone book'))]

    command_options = [
        # command options
        make_option('--list', action='command',
                    options=['--sort-by', '--ignore-case'],
                    help=_('print a short list of the specified entries')),
        make_option('--table', action='command',
                    help=_('print a table with the specified entries.'),
                    options=['--output', '--sort-by', '--ignore-case']),
        make_option('--show', action='command',
                    options=['--sort-by', '--ignore-case'],
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
                    help=_('ignore case, when searching or sorting. The '
                           'default is not to ignore case.')),
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
            if not os.path.exists(tel.CONFIG.CONFIG_DIR):
                os.mkdir(tel.CONFIG.CONFIG_DIR)
            (options, args) = self._parse_args()
            self.phonebook = phonebook.PhoneBook(options.file)
            options.command_function(options, *args)
        except KeyboardInterrupt:
            sys.exit(_('Dying peacefully ...'))

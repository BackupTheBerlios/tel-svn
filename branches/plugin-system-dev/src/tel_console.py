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
# THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""This is the command line front end to tel"""

__revision__ = '$Id$'

import os
import sys
import itertools
import textwrap
import re

try:
    # more comfortable line editing
    import readline
except ImportError:
    pass

# tel modules
from tel import phonebook, encodinghelper, config
from tel.cmdoptparse import CommandOptionParser, make_option


encodinghelper.redirect_std_streams(True)
_ = config.translation.ugettext


class ConsoleEntryEditor(object):
    """This class provides a simple console-based entry editor.

    :ivar current_field: The name of the currently edited field"""

    EDIT_MSG = _('Editing entry "%s"...')
    NEW_MSG = _('Creating a new entry...')

    def __init__(self, fields, new=False):
        """`fields` is a list of fields to be edited by this editor.
        Set `new` to True, if you are mainly editing new entries.
        This only affects the printed help, ConsoleEntryEditor detects
        automatically, if a single entry is new"""
        self.print_help(new)
        self.fields = fields
        
    def edit(self, entry):
        """Edits `entry`.
        :returns: The edited `entry`"""
        new = entry.parent is None
        if new:
            # entry is new
            print self.NEW_MSG
        else:
            print self.EDIT_MSG % entry

        self.initialize_editor()
        for field in self.fields:
            oldvalue = entry[field]
            while True:
                value = self.get_input(field, oldvalue, new)
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
            print _('Please fill the following fields.')

        def initialize_editor(self):
            """Initialize the editor"""
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
            prompt = u'%s: ' % phonebook.translate_field(field)
            return raw_input(prompt)
            
        def _input_hook(self):
            """displays the current value in the input line"""
            if self.oldvalue:
                readline.insert_text(self.oldvalue)
                readline.redisplay()
        
    except NameError:

        # don't do anything
        def initialize_editor(self):
            pass
        finalize_editor = initialize_editor
        
        def print_help(self, new):
            """Print a little editing help"""
            if new:
                help = _('Please fill the following fields.')
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
            return raw_input(prompt)
            

# output and utility functions
def print_short_list(entries):
    """Prints all `entries` in a short format."""
    print
    for entry in entries:
        print entry


def print_long_list(entries):
    """Prints every single entry in `entries` in full detail.
    :param sortby: The field to sort by
    :param asc: True, if sorting order is descending"""
    for entry in entries:
        print '-'*20
        print entry.prettify()


def print_table(entries, fields):
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
    headline = itertools.imap(unicode.center, headline, column_widths)
    headline = u'| %s |' % u' | '.join(headline)
    separator = (u'-'*(width+2) for width in column_widths)
    separator = u'|%s|' % u'+'.join(separator)
    print headline
    print separator
    for row in table_body:
        row = itertools.imap(unicode.ljust, row, column_widths)
        row = u'| %s |' % u' | '.join(row)
        print row


def yes_no_question(question):
    """Asks `question` as a yes/no question. Returns True, if the user
    answered yes, otherwise False."""
    promt = _('%(question)s [%(yes)s,%(no)s] ') % {'question': question,
                                                   'yes': _('y'),
                                                   'no': _('n')}
    return (raw_input(promt).lower() == _('y'))


class ConsoleIFace(object):
    """Provides a console interface to Tel"""

    def __init__(self):
        self.phonebook = None

    def edit_entries(self, entries):
        """Allows interactive editing of entries. If `new` is True, `entry`
        is identified as new entry"""
        editor = ConsoleEntryEditor(self.phonebook.supported_fields(),
                                    bool(entries[0].parent))
        for entry in entries:
            entry = editor.edit(entry)
            # check if the user wants to add an empty entry
            if not entry:
                question = _('Do you really want to save an emtpy entry?')
                if not yes_no_question(question):
                    # abort without saving
                    print _('The entry is not saved')
                    return
            if entry.parent is None:
                self.phonebook.add(entry)
            self.phonebook.save()
            print _('The entry was saved')

    def _find_entries(self, options, *args):
        """Finds entries according to command line arguments"""
        entries = self.phonebook
        if args:
            patterns = args
            if options.regexp:
                flags = re.UNICODE
                if options.ignore_case:
                    flags |= re.IGNORECASE
                patterns = (re.compile(pat, flags) for pat in patterns)
            # FIXME: implement options.ignore_case for non-re patterns
            entries = []
            for pat in patterns:
                entries.extend(self.phonebook.find_all(pat,
                                                       *options.fields))
        # remove double entries
        return list(set(entries))

    def _get_entries_from_options(self, options, *args):
        """Analyzes arguments and options, and returns a list of entries
        that should be worked with"""
        # sort entries
        return phonebook.sort_by_field(self._find_entries(options, *args),
                                        # the field to sort by
                                       options.sortby[0],
                                       # ascending or descending
                                       options.sortby[1], 
                                       options.ignore_case)
        

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

##     def _cmd_export(self, options, *args):
##         """Exports phone book"""
##         for path in args:
##             if not os.path.exists(path) and not os.path.basename(path):
##                 # create non-existing directories here, if the user wants it
##                 msg = _('Directory %s does not exist. Create it? ')
##                 resp = raw_input(msg % path)
##                 if resp.lower() == 'y':
##                     os.makedirs(path)
##                 else:
##                     # do not export
##                     continue
##             if os.path.isdir(path):
##                 # if path is a directory, create the export target by
##                 # joining the filename of the phone book with the path
##                 filename = os.path.basename(self.phonebook.path)
##                 path = os.path.join(path, filename)
##             if os.path.isfile(path):
##                 # now check, if the file denoted by path already exists
##                 msg = _('%s already exists. Overwrite it? ')
##                 resp = raw_input(msg % path)
##                 if resp.lower() != 'y':
##                     continue
##             try:
##                 shutil.copyfile(self.phonebook.path, path)
##             except IOError, e:
##                 if e.errno == 13:
##                     msg = _('Error: Permission denied for %s') % path
##                 else:
##                     msg = e
##                 print >> sys.stderr, msg

##     def _cmd_import(self, options, *args):
##         """Import phone books"""
##         for path in args:
##             # import all specified phone books
##             if os.path.exists(path):
##                 if (os.path.abspath(path) ==
##                     os.path.abspath(self.phonebook.path)):
##                     resp = raw_input(_('Do you really want to import the '
##                                        'phone book you\'re just using? '))
##                     if resp.lower() != 'y':
##                         print _('Not importing %s...') % path
##                         continue
##                 import_book = phonebook.PhoneBook(path)
##                 for entry in import_book:
##                     # enable auto-generation of index
##                     entry.index = None
##                     self.phonebook.add(entry)
##         self.phonebook.save()      

    def _cmd_table(self, options, *args):
        """Print a table"""
        entries = self._get_entries_from_options(options, *args)
        print_table(entries, options.output)

    def _cmd_list(self, options, *args):
        """Print a short list of entries"""
        entries = self._get_entries_from_options(options, *args)
        print_short_list(entries)

    def _cmd_show(self, options, *args):
        """Shows entries"""
        entries = self._get_entries_from_options(options, *args)
        print_long_list(entries)

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
        entries = [Entry() for Entry in itertools.repeat(phonebook.Entry,
                                                         number)]
        self.edit_entries(entries)

    def _cmd_edit(self, options, *args):
        """Interactivly edit entries"""
        entries = self._find_entries(options, *args)
        if not entries:
            sys.exit(_('No entries found for given patterns'))
        self.edit_entries(entries)

    def _cmd_remove(self, options, *args):
        for entry in self._find_entries(options, *args):
            resp = raw_input(_('Really delete entry "%s"? ') % entry)
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
        'file': os.path.join(config.user_directory, 'phonebook.csv'),
        'output': phonebook.FIELDS,
        'ignore_case': False,
        'sortby': ('lastname', False),
        'fields': phonebook.FIELDS
        }

    global_options = [
        # These options tune the behaviour of all commands
        make_option('-f', '--file', action='store', dest='file',
                    metavar=_('file'), help=_('use FILE as phone book'))]

    command_options = [
        # command options
        make_option('--list', action='command',
                    options=['--sort-by', '--ignore-case', '--regexp',
                             '--fields'],
                    help=_('print a short list of the specified entries')),
        make_option('--table', action='command',
                    help=_('print a table with the specified entries.'),
                    options=['--output', '--sort-by', '--ignore-case',
                             '--regexp', '--fields']),
        make_option('--show', action='command',
                    options=['--sort-by', '--ignore-case', '--regexp',
                             '--fields'],
                    help=_('show the specified entries')),
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

    search_options = [
        # These options tune the searching behaviour
        make_option('-r', '--regexp', action='store_true', dest='regexp',
                    help=_('enable regular expressions. tel uses the '
                           'Python-syntax. You can find an overview at the '
                           'following URL: '
                           'http://docs.python.org/lib/re-syntax.html')),
        make_option('-i', '--ignore-case', action='store_true',
                    dest='ignore_case',
                    help=_('ignore case, when searching or sorting. The '
                           'default is not to ignore case.')),
        # FIXME: someone knows a good short options for --fields?
        make_option('--fields', action='store', dest='fields',
                    type='field_list', metavar=_('fields'),
                    help=_('specify a list of fields to search in. Takes a '
                           'comma-separated list of internal names as '
                           'printed by --help-fields. Fields prefixed with '
                           '"-" are hidden.'))
        ]

    local_options = [
        # these options tune the behaviour of some commands
        make_option('-s', '--sort-by', type='field', dest='sortby',
                    metavar=_('field'),
                    help=_('sort output. Specify a field name as printed '
                           'by --help-fields. If prefixed with +, sorting '
                           'order is ascending, if prefixed with a -, '
                           'sorting order is descending. The default is '
                           'ascending, if no prefix is used.')),
        make_option('-o', '--output', action='store', dest='output',
                    type='field_list', metavar=_('fields'), 
                    help=_('specify the fields to show. '
                           'See --search option for syntax'))
        ]

    def _parse_args(self):
        """Parses command line arguments"""
        parser = CommandOptionParser(prog='tel',
                                     usage=self.usage,
                                     description=self.description,
                                     version=config.version,
                                     authors=config.authors,
                                     license=config.license,
                                     copyright=config.copyright)
        # command options
        desc = _('Commands to modify the phone book and to search or '
                 'print entries. Only one of these options may be '
                 'specified.\n'
                 'Entries are specified through searching patterns. '
                 'See searching options for details')
        group = parser.add_option_group(_('Commands'), desc)
        group.add_options(self.command_options)
        # searching options
        desc = _('These options apply to every command, that deals with '
                 'entries. They tune the search of entries')
        group = parser.add_option_group(_('Searching options'), desc)
        group.add_options(self.search_options)
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
            self.phonebook = phonebook.phonebook_open(options.file)
            self.phonebook.load()
            options.command_function(options, *args)
        except KeyboardInterrupt:
            sys.exit(_('Dying peacefully ...'))


def main():
    ConsoleIFace().start()

if __name__ == '__main__':
    main()

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
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
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
import locale

# tel modules
from tel import phonebook, config
from tel.cmdoptparse import CommandOptionParser, make_option
# encoding stuff
from tel.encodinghelper import stdout_encoding, exit, raw_input


_ = config.translation.ugettext


try:
    import readline
    have_readline = True
except ImportError:
    msg = _('readline wasn\'t found, text editing capabilities are '
            'restricted.')
    print >> sys.stderr, msg
    have_readline = False


class ConsoleEntryEditor(object):
    """This class provides a simple console-based entry editor.

    :ivar current_field: The name of the currently edited field"""

    EDIT_MSG = _('Editing entry "%s" ...')
    NEW_MSG = _('Creating a new entry ...')

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
        print
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


    if have_readline:
        # input methods supporting readline
        def print_help(self, new):
            print _('Please fill the following fields!')

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
                text = self.oldvalue.encode(stdout_encoding)
                readline.insert_text(text)
                readline.redisplay()

    else:
        # don't do anything

        def initialize_editor(self):
            pass
        finalize_editor = initialize_editor

        def print_help(self, new):
            """Print a little editing help"""
            if new:
                help = _('Please fill the following fields!')
            else:
                help = _('Please fill the following fields! The current '
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

def print_entries_table(entries, fields):
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


def print_simple_table(headline, items):
    """Prints a simple table with `headline` and `items`"""
    column_widths = map(len, headline)
    for item in items:
        column_widths = map(max, map(len, item), column_widths)
    headline = itertools.imap(unicode.center, headline, column_widths)
    headline = ' %s' % u' - '.join(headline)
    print headline
    # a separator
    print u'-' * (column_widths[0] + column_widths[1] + 5)
    for item in items:
        item = itertools.imap(unicode.ljust, item, column_widths)
        print ' %s' % u' - '.join(item)


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
                    print _('The entry is not saved.')
                    return
            if entry.parent is None:
                self.phonebook.add(entry)
            try:
                self.phonebook.save()
                print _('The entry was saved.')
            except Exception, exp:
                msg = (exp.strerror if isinstance(exp, EnvironmentError)
                       else exp.message)
                exit(_('Couldn\'t save the phonebook: %s') % msg)


    def _find_entries(self, options, *args):
        """Finds entries according to command line arguments"""
        entries = self.phonebook
        if not args:
            return entries

        patterns = args
        flags = re.UNICODE
        if options.ignore_case:
            flags |= re.IGNORECASE
        patterns = (re.compile(pat, flags) for pat in patterns)
        entries = []
        for pat in patterns:
            entries.extend(self.phonebook.find_all(pat, *options.fields))
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

    def _cmd_table(self, options, *args):
        """Print a table"""
        entries = self._get_entries_from_options(options, *args)
        print_entries_table(entries, options.output)

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
                exit(_('--create needs a number.'))
        if len(args) > 1:
            exit(_('--create only accepts one argument.'))
        entries = [Entry() for Entry in itertools.repeat(phonebook.Entry,
                                                         number)]
        self.edit_entries(entries)

    def _cmd_edit(self, options, *args):
        """Interactivly edit entries"""
        entries = self._find_entries(options, *args)
        if not entries:
            exit(_('No entries found for given patterns.'))
        self.edit_entries(entries)

    def _cmd_remove(self, options, *args):
        for entry in self._find_entries(options, *args):
            if yes_no_question(_('Really delete entry "%s"?') % entry):
                self.phonebook.remove(entry)
        self.phonebook.save()

    def _cmd_help_fields(self, options, *args):
        if not args:
            args = phonebook.FIELDS
        try:
            items = [(phonebook.translate_field(field), unicode(field))
                     for field in args]
        except phonebook.NoSuchField, e:
            exit(_('There is no field %s.') % e.field)

        headline = [_('Field'), _('Internal name')]
        print_simple_table(headline, items)

    def _cmd_help_backends(self, options, *args):
        if len(args) > 1:
            exit(_('Please specifiy only one backend!'))
        from tel import backendmanager
        manager = backendmanager.manager()
        if not args:
            items = [(unicode(backend.__name__),
                      backend.__short_description__)
                     for backend in manager.itervalues()]
            headline = [_('Backend name'), _('Description')]
            print_simple_table(headline, items)
        else:
            try:
                # print complete description for a single backend
                backend = manager[args[0]]
            except KeyError, e:
                exit(e.message)
            fields = backend.__phonebook_class__.supported_fields()
            wrap = textwrap.TextWrapper(79)
            info = {'name': backend.__name__,
                    'shortdesc': wrap.fill(backend.__short_description__),
                    'longdesc': wrap.fill(backend.__long_description__),
                    'fields': wrap.fill(', '.join(fields))
                    }
            print _("""
%(name)s - %(shortdesc)s
------------

Supported fields:
%(fields)s

------------

%(longdesc)s""") % info


    ## COMMAND SUPPORT FUNCTIONS

    def _get_cmd_function(self, arg):
        """Returns the function for `arg`"""
        return getattr(self, '_cmd_'+arg)

    # OPTION PARSING

    usage = _('%prog [options] command [arguments]')

    description = _('tel is a little address book program for your '
                    'terminal.')

    defaults = {
        'uri': 'csv://' + os.path.join(config.user_directory,
                                       'phonebook.csv'),
        'output': phonebook.FIELDS,
        'ignore_case': False,
        'sortby': ('lastname', False),
        'fields': phonebook.FIELDS
        }

    global_options = [
        # These options tune the behaviour of all commands
        make_option('-u', '--uri', action='store', dest='uri',
                    metavar=_('uri'), help=_('load phonebook from URI.')),
        ]

    command_options = [
        # command options
        make_option('--list', action='command',
                    options=('--sort-by', '--ignore-case', '--fields'),
                    help=_('print a short list of the specified entries.')),
        make_option('--table', action='command',
                    help=_('print a table with the specified entries.'),
                    options=('--output', '--sort-by', '--ignore-case',
                             '--fields')),
        make_option('--show', action='command',
                    options=('--sort-by', '--ignore-case', '--fields'),
                    help=_('show the specified entries.')),
        make_option('--create', action='command', metavar=_('number'),
                    help=_('create the specified number of new entries.')),
        make_option('--edit', action='command', args='required',
                    help=_('edit the specified entries.')),
        make_option('--remove', action='command', args='required',
                    help=_('remove the specified entries.')),
        ## make_option('--export', action='command', args='required',
        ##             help=_('export phone book to all specified locations.'),
        ##             metavar=_('targets')),
        ## make_option('--import', action='command', args='required',
        ##             help=_('import all specified phone books.'),
        ##             metavar=_('files'))
        ]

    search_options = [
        make_option('-i', '--ignore-case', action='store_true',
                    dest='ignore_case',
                    help=_('ignore case, when searching or sorting. The '
                           'default is not to ignore case.')),
        make_option('-f', '--fields', action='store', dest='fields',
                    type='field_list', metavar=_('fields'),
                    help=_('specify a list of fields to search in. Takes a '
                           'comma-separated list of internal names as '
                           'printed by --help-fields. Fields prefixed with '
                           '"-" are not searched.'))
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
                    help=_('specify the fields to show. Uses the same '
                           'syntax as the --fields option.'))
        ]

    def _parse_args(self, args):
        """Parses command line arguments"""
        parser = CommandOptionParser(prog='tel',
                                     usage=self.usage,
                                     description=self.description,
                                     version=config.version,
                                     authors=config.authors,
                                     license=config.license,
                                     copyright=config.copyright)
        parser.add_option('--help-backends', action='command',
                          args='optional', metavar=_('backends'))
        parser.add_option('--help-fields', action='command',
                          args='optional', metavar=_('fields'))
        # command options
        desc = _('Commands to modify the phone book and to search or '
                 'print entries. Only one of these options may be '
                 'specified.\n'
                 'Entries are specified through regular expressions. '
                 'See http://docs.python.org/lib/re-syntax.html for a '
                 'description of regular expression syntax.')
        group = parser.add_option_group(_('Commands'), desc)
        group.add_options(self.command_options)
        # searching options
        desc = _('These options apply to every command, that deals with '
                 'entries. They tune the search for entries.')
        group = parser.add_option_group(_('Searching options'), desc)
        group.add_options(self.search_options)
        # global options
        desc = _('These options are valid with every command.')
        group = parser.add_option_group(_('Global options'), desc)
        group.add_options(self.global_options)
        desc = _('These options are only supported by certain commands. If '
                 'you use them with other commands, they are just ignored.')
        group = parser.add_option_group(_('Special options'), desc)
        group.add_options(self.local_options)

        parser.set_defaults(**self.defaults)
        (options, args) = parser.parse_args(args[1:])

        if not hasattr(options, 'command'):
            parser.error(_('Please specify a command!'))

        if options.args == 'required' and not args:
            msg = _('The command %s need arguments.')
            parser.error(msg % options.command)
        elif options.args == 'no' and args:
            msg = _('The command %s doesn\'t take any arguments.')
            parser.error(msg % options.command)

        # get the command function
        options.command_function = self._get_cmd_function(options.command)
        return (options, args)

    def start(self):
        """Starts the interface"""
        try:
            locale.setlocale(locale.LC_ALL, '')
            args = [arg.decode(sys.getfilesystemencoding()) for arg in
                    sys.argv]
            (options, args) = self._parse_args(args)
            try:
                self.phonebook = phonebook.phonebook_open(options.uri)
                self.phonebook.load()
            except Exception, exp:
                msg = (_('Couldn\'t load %(uri)s: %(message)s') %
                         {'message': exp.message,
                          'uri': (getattr(self.phonebook, 'uri', None)
                                  or options.uri)})
                exit(msg)
            options.command_function(options, *args)
        except KeyboardInterrupt:
            exit(_('Dying peacefully ...'))


if __name__ == '__main__':
    ConsoleIFace().start()

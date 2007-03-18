#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# extended optparse module to support commands
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

"""This module provides an extended OptionParser class, which supports
things like command options"""

__revision__ = '$Id$'


import sys
import optparse
import gettext
import textwrap

from copy import copy
from optparse import (Option, OptionError, OptionParser, OptionValueError,
                      IndentedHelpFormatter, OptionGroup)

import phonebook


_ = gettext.translation('tel').ugettext


class CommandHelpFormatter(IndentedHelpFormatter):
    """A Formatter, which respects certain command properties
    like args"""

    def format_option(self, option):
        """Extend option formatting to include formatting of supported
        options."""
        result = IndentedHelpFormatter.format_option(self, option)
        if option.action == 'command' and option.options:
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
        if option.action == 'command' and not option.args == 'no':
            arg_name = option.metavar or _('indices')
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
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    CHECK_METHODS = Option.CHECK_METHODS[:]
    ACTIONS = Option.ACTIONS[:]
    ATTRS = Option.ATTRS[:]
    TYPES = Option.TYPES[:]
    TYPES += ('field_list', 'field')
    ATTRS += ['args', 'options']
    ACTIONS += ('copyright', 'authors', 'license', 'command',
                'print_fields')

    def _check_attrs(self):
        if self.action == 'command':
            if self.args is None:
                self.args = 'optional'
            elif self.args not in ('optional', 'required', 'no'):
                raise OptionError("args must be on of: 'optional', "
                                  "'required', no'", self)
        elif self.args is not None:
            raise OptionError("'args' must not be supplied for action "
                              "%r" % self.action, self)

    def _check_options(self):
        if self.action == 'command':
            if self.options and not isinstance(self.options, (tuple, list)):
                raise OptionError('options must be a tuple or a list', self)
        elif self.options is not None:
            raise OptionError("'options' must not be supplied for action "
                              "%r" % self.action, self)

    def _check_field_list(self, opt, value):
        """Parse field_list options into a list of fields"""
        warning_msg = _('')
        items = map(str.strip, value.split(','))
        # filter empty fields
        # (which came from something like "index,,firstname")
        items = filter(None, items)
        fields_to_show = []
        fields_to_hide = []
        for item in items:
            fieldname = item.lstrip('-')
            if fieldname not in phonebook.FIELDS:
                raise OptionValueError('There is no field %s' % fieldname)
            if item.startswith('-'):
                fields_to_hide.append(fieldname)
            else:
                fields_to_show.append(fieldname)
        if not fields_to_show:
            fields_to_show = list(phonebook.FIELDS)
        for field in fields_to_hide:
            if field in fields_to_show:
                fields_to_show.remove(field)
        return fields_to_show

    def _check_field(self, opt, value):
        """Parse a field into a tuple containing the field in the first and
        the sorting order (True if descending) in the second field"""
        fieldname = value.lstrip('+-')
        if not fieldname in phonebook.FIELDS:
            raise OptionValueError('There is no field %s' % fieldname)
        else:
            return (fieldname, value.startswith('-'))
            
    CHECK_METHODS += [_check_attrs, _check_options]
    TYPE_CHECKER['field_list'] = _check_field_list
    TYPE_CHECKER['field'] = _check_field

    def take_action(self, action, dest, opt, value, values, parser):
        """Executes `action`"""
        if action == 'license':
            parser.print_license()
            parser.exit()
        elif action == 'copyright':
            parser.print_copyright()
            parser.exit()
        elif action == 'authors':
            parser.print_authors()
            parser.exit()
        elif action == 'print_fields':
            parser.print_fields()
            parser.exit()
        elif action == 'command':
            if hasattr(parser.values, 'command'):
                # raise error if two exlusive commands appeared
                msg = _('Please specify only one command option')
                raise OptionValueError(msg)
            values.command = opt.lstrip('-').replace('-', '_')
            values.command_values = value
            values.args = self.args
        else:
            return Option.take_action(self, action, dest, opt, value,
                                      values, parser)
        return True


make_option = CommandOption
    

#FIXME: we could verify options and args keyword for commands

class CommandOptionParser(OptionParser):
    """An option parser, which supports things like command options"""

    def __init__(self, usage=None, option_list=None, version=None,
                 option_class=CommandOption, conflict_handler="error",
                 description=None, formatter=None, add_help_option=True,
                 prog=None, license=None, copyright=None, authors=None):
        """:param license: license information
        :param copyright: copyright information
        :param authors: list or tuple of authors"""
        if not formatter:
            formatter = CommandHelpFormatter()
            
        self.authors = authors
        self.license = license
        self.copyright = copyright
        
        OptionParser.__init__(self, usage, option_list, option_class,
                              version, conflict_handler, description,
                              formatter, add_help_option, prog)
        
    def _populate_option_list(self, option_list, add_help=True):
        OptionParser._populate_option_list(self, option_list, add_help)
        if self.authors:
            self.add_option('--authors', action='authors',
                            help=_('show author information and exit'))
        if self.license:
            self.add_option('--license', '--licence', action='license',
                            help=_('show program\'s license and exit'))
        if self.copyright:
            self.add_option('--copyright', action='copyright',
                            help=_('show copyright information and exit'))
        self.add_option('--print-fields', action='print_fields',
                        help=_('print fields and exit'))

    def add_option_group(self, *args, **kwargs):
        """Adds a new option group"""
        if isinstance(args[0], unicode):
            group = OptionGroup(self, *args, **kwargs)
            args = [group]
            kwargs = {}
        return OptionParser.add_option_group(self, *args, **kwargs)

    def error(self, msg):
        """Print a usage message incorporating 'msg' to stderr and exit."""
        # from OptionParser, 'cause i18n is missing for message
        self.print_usage(sys.stderr)
        self.exit(2, _('%s: error: %s\n') % (self.get_prog_name(), msg))

    def get_license(self):
        """Returns license information"""
        if self.license:
            return self.expand_prog_name(self.license)
        else:
            return ''

    def get_authors(self):
        """Returns author information as string"""
        if self.authors:
            return '\n'.join(self.authors)
        else:
            return ''

    def get_copyright(self):
        """Return copyright information"""
        if self.copyright:
            return self.expand_prog_name(self.copyright)
        else:
            return ''

    def get_fields(self):
        """Return a table of field names"""
        items = [(phonebook.translate_field(field), field) for field in
                 phonebook.FIELDS]
        headline = [_('Field'), _('Internal name')]
        column_widths = map(len, headline)
        for item in items:
            column_widths = map(max, map(len, item), column_widths)
        headline = ' - '.join(map(lambda item, width: item.center(width),
                                  headline, column_widths))
        separator = '-' * (column_widths[0] + column_widths[1] + 5)
        table = [' '+headline, separator]
        for item in items:
            item = ' - '.join(map(lambda item,width: item.ljust(width),
                                  item, column_widths))
            table.append(' '+item)
        return '\n'.join(table)

    def print_license(self, stream=None):
        """Prints license information to `stream`"""
        if self.license:
            print >> stream, self.get_license()

    def print_authors(self, stream=None):
        """Prints author information to `stream`"""
        if self.authors:
            print >> stream, self.get_authors()

    def print_copyright(self, stream=None):
        """Print copyright information to `stream`"""
        if self.copyright:
            print >> stream, self.get_copyright()

    def print_fields(self, stream=None):
        """Print field information to `stream`"""
        print >> stream, self.get_fields()

    def print_help(self, stream=None):
        """Print help to`stream`"""
        print >> stream, self.format_help()
                   

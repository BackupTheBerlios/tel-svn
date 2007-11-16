# -*- coding: utf-8 -*-
# extended optparse module to support commands
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

"""This module provides an extended OptionParser class, which supports
things like command options"""


__revision__ = '$Id$'


import sys
import optparse
import textwrap

from copy import copy

import optparse
from optparse import (Option, OptionError, OptionParser, OptionValueError,
                      IndentedHelpFormatter, OptionGroup, BadOptionError,
                      OptionValueError)

from tel import phonebook
from tel import config
from tel.encodinghelper import stdout, stderr

# make optparse use our improved gettext ;)
_ = optparse._ = config.translation.ugettext


class CommandHelpFormatter(IndentedHelpFormatter):
    """A Formatter, which respects certain command properties
    like args"""

    def format_option(self, option):
        """Extend option formatting to include formatting of supported
        options."""
        result = IndentedHelpFormatter.format_option(self, option)
        if option.action == 'command' and option.options:
            options = ', '.join(option.options)
            msg = _('Supported options: ')
            # build the complete options string and wrap it to width of the
            # help
            opt_str = ''.join((msg, options))
            initial_indent = ' '*(self.help_position + 4)
            subsequent_indent = ' '*(self.help_position + 4 + len(msg))
            width = self.help_position + self.help_width
            opt_str = textwrap.fill(opt_str, width,
                                    initial_indent=initial_indent,
                                    subsequent_indent=subsequent_indent)
            result += opt_str + '\n'
        return result


    def format_option_strings(self, option):
        """Extend option string formatting to support arguments for
        commands"""
        if option.action == 'command' and not option.args == 'no':
            arg_name = option.metavar or _('pattern')
            if option.args == 'optional':
                arg_name = ''.join(('[', arg_name, ']'))
            lopts = (' '.join([lopt, arg_name]) for lopt in
                     option._long_opts)
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
    ACTIONS += ('copyright', 'authors', 'license', 'command')

    def _check_attrs(self):
        if self.action == 'command':
            if self.args is None:
                self.args = 'optional'
            elif self.args not in ('optional', 'required', 'no'):
                raise OptionError("args must be one of: 'optional', "
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
        items = map(lambda item: item.strip(), value.split(','))
        # filter empty fields
        # (which came from something like "index,,firstname")
        items = filter(None, items)
        fields_to_show = []
        fields_to_hide = []
        for item in items:
            fieldname = item.lstrip('-')
            if fieldname not in phonebook.FIELDS:
                raise OptionValueError('There is no field %s.' % fieldname)
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
            raise OptionValueError('There is no field %s.' % fieldname)
        else:
            return (fieldname, value.startswith('-'))

    CHECK_METHODS += [_check_attrs, _check_options]
    TYPE_CHECKER['field_list'] = _check_field_list
    TYPE_CHECKER['field'] = _check_field

    def take_action(self, action, dest, opt, value, values, parser):
        """Executes `action`"""
        if action == 'license':
            parser.print_license(stdout)
            parser.exit()
        elif action == 'copyright':
            parser.print_copyright(stdout)
            parser.exit()
        elif action == 'authors':
            parser.print_authors(stdout)
            parser.exit()
        elif action == 'help':
            parser.print_help(stdout)
            parser.exit()
        elif action == 'command':
            if hasattr(parser.values, 'command'):
                # raise error if two exlusive commands appeared
                msg = _('Please specify only one command option!')
                raise OptionValueError(msg)
            values.command = opt.lstrip('-').replace('-', '_')
            values.command_values = value
            values.args = self.args
        else:
            return Option.take_action(self, action, dest, opt, value,
                                      values, parser)
        return True


make_option = CommandOption


# XXX: we could verify options and args keyword for commands

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
                            help=_('show author information and exit.'))
        if self.license:
            self.add_option('--license', '--licence', action='license',
                            help=_('show program\'s license and exit.'))
        if self.copyright:
            self.add_option('--copyright', action='copyright',
                            help=_('show copyright information and exit.'))

    def error(self, msg):
        """Print a usage message incorporating 'msg' to stderr and exit."""
        # reimplemented to support i18n and unicode
        self.print_usage(sys.stderr)
        pattern = _('%(prog)s: error: %(message)s')
        self.exit(2, pattern % {'prog': self.get_prog_name(),
                                'message': msg})

    def exit(self, status=0, msg=None):
        # reimplemented to support unicode
        if msg:
            print >> stderr, msg
        sys.exit(status)

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

    def add_option_group(self, *args, **kwargs):
        if isinstance(args[0], basestring):
            group = OptionGroup(self, *args, **kwargs)
            return OptionParser.add_option_group(self, group)
        else:
            return OptionParser.add_option_group(self, *args, **kwargs)

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

    def parse_args(self, args=None, values=None):
        """
        parse_args(args : [string] = sys.argv[1:],
                   values : Values = None)
        -> (values : Values, args : [string])

        Parse the command-line options found in 'args' (default:
        sys.argv[1:]).  Any errors result in a call to 'error()', which
        by default prints the usage message to stderr and calls
        sys.exit() with an error message.  On success returns a pair
        (values, args) where 'values' is an Values instance (with all
        your option values) and 'args' is the list of arguments left
        over after parsing options.
        """
        # reimplemented to support unicode
        rargs = self._get_args(args)
        if values is None:
            values = self.get_default_values()

        # Store the halves of the argument list as attributes for the
        # convenience of callbacks:
        #   rargs
        #     the rest of the command-line (the "r" stands for
        #     "remaining" or "right-hand")
        #   largs
        #     the leftover arguments -- ie. what's left after removing
        #     options and their arguments (the "l" stands for "leftover"
        #     or "left-hand")
        self.rargs = rargs
        self.largs = largs = []
        self.values = values

        try:
            stop = self._process_args(largs, rargs, values)
        except (BadOptionError, OptionValueError), err:
            self.error(unicode(err))

        args = largs + rargs
        return self.check_values(values, args)

    def print_help(self, stream=None):
        """
        Prints help
        """
        if stream is None:
            stream = stdout
        stream.write(self.format_help())

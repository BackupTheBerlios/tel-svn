#!/usr/bin/env python
# -*- coding: utf-8 -*-
# main module


"""Contains globale configuration and provides the starter script for tel.

:mvar config: Stores a global configuration object, which provides access to
all important configuration settings."""

__revision__ = '$Id$'

__license_name__ = 'MIT/X11'
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
__version__ = '0.1.7-pre1'
__authors__ = ('Sebastian Wiesner <basti.wiesner@gmx.net>',
               'Remo Wenger <potrmwn@gmail.com>')


import sys
import os
import gettext
# make sure, empty finds its way into global namespace
import teltypes

class _Configuration(object):
    """This object stores configuration.
    Currently it only knows about hard-coded installation paths, which are
    replaced during the installation process."""

    _messages = '${install_messages}'
    _appmodules = '${install_app_modules}'
    _user_directory = None
    _copyright = None
    _translation = None
    _backend_directories = None
    _pretty_entry_format = None
    
    @property
    def messages(self):
        """Installation directory of gettext messsage catalogs"""
        # make sure, that configuration is useable, even if placeholders
        # were not replaced
        if os.path.isdir(self._messages):
            return self._messages
        return None

    @property
    def stdout_encoding(self):
        """Encoding of standard output stream"""
        return sys.stdout.encoding or sys.getfilesystemencoding()

    @property
    def stdin_encoding(self):
        """Encoding of standard input stream"""
        return sys.stdin.encoding or sys.getfilesystemencoding()

    @property
    def appmodules(self):
        """Installation directory of tel modules"""
        if os.path.isdir(self._appmodules):
            return self._appmodules
        else:
            return os.path.dirname(__file__)

    @property
    def user_directory(self):
        """Configuration directory in user's home directory.
        The directory is created, if necessary"""
        # create user directory, if necessary
        if not self._user_directory:
            directory = os.path.join('~', '.tel')
            self._user_directory = os.path.expanduser(directory)
        if not os.path.isdir(self._user_directory):
            os.mkdir(self._user_directory)
        return self._user_directory

    @property
    def version(self):
        """tel's version"""
        return __version__

    @property
    def license(self):
        """tel's license"""
        return __license__

    @property
    def license_name(self):
        """the name of tel's license"""
        return __license_name__

    @property
    def authors(self):
        """a tuple of all authors"""
        return __authors__

    @property
    def copyright(self):
        """The copyright notice of tel"""
        if not self._copyright:
            self._copyright = __license__.splitlines()[0]
        return self._copyright

    @property
    def translation(self):
        """The gettext translation class for tel"""
        if self._translation is None:
            self._translation = gettext.translation('tel', config.messages,
                                                    fallback=True)
        return self._translation

    @property
    def backend_directories(self):
        """Directories which are searched for storage backends"""
        if self._backend_directories is None:
            # default directory
            def_dirs = [os.path.join(self.appmodules, 'backends'),
                        os.path.join(self.user_directory, 'backends')]
            self._backend_directories = def_dirs
        return self._backend_directories

    @property
    def pretty_entry_format(self):
        """A nice readable entry format"""
        if not self._pretty_entry_format:
            msg = _('Name:           %(title)s %(firstname)s %(lastname)s\n'
                    'Address:        %(street)s\n'
                    '                %(country)s, %(postcode)s %(town)s\n'
                    'POB:            %(postbox)s\n'
                    'E-Mail:         %(email)s\n'
                    'Phone:          %(phone)s\n'
                    'Mobile:         %(mobile)s\n'
                    'Date of birth:  %(birthdate)s\n'
                    'Tags:           %(tags)s\n')
            self._pretty_entry_format = msg
        return self._pretty_entry_format

    
# create the global configuration object
config = _Configuration()


sys.path.append(config.appmodules)
_ = config.translation.ugettext


if __name__ == '__main__':
    # tel modules
    from consoleiface import ConsoleIFace
    ConsoleIFace().start()

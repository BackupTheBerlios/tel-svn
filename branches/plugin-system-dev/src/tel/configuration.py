#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import gettext

# make global stuff like license and copyright available
import tel


class Configuration(object):
    """This object stores configuration.
    Currently it only knows about hard-coded installation paths, which are
    replaced during the installation process."""

    _messages = '${install_messages}'
    _appmodules = '${install_app_modules}'
    _user_directory = None
    _copyright = None
    _translation = None
    _backend_directories = None
    _long_entry_format = None
    _short_entry_format = None

    @property
    def messages(self):
        """Installation directory of gettext messsage catalogs"""
        # make sure, that configuration is useable, even if placeholders
        # were not replaced
        if os.path.isdir(self._messages):
            return self._messages
        return None

    @property
    def appmodules(self):
        """Installation directory of tel modules"""
        if os.path.isdir(self._appmodules):
            return self._appmodules
        else:
            return os.getcwd()

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
        return tel.__version__

    @property
    def license(self):
        """tel's license"""
        return tel.__license__

    @property
    def license_name(self):
        """the name of tel's license"""
        return tel.__license_name__

    @property
    def authors(self):
        """a tuple of all authors"""
        return tel.__authors__

    @property
    def copyright(self):
        """The copyright notice of tel"""
        if not self._copyright:
            self._copyright = tel.__license__.splitlines()[0]
        return self._copyright

    @property
    def translation(self):
        """The gettext translation class for tel"""
        if self._translation is None:
            self._translation = gettext.translation('tel', self.messages,
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
    def long_entry_format(self):
        """A nice readable entry format"""
        if not self._long_entry_format:
            _ = self.translation.ugettext
            msg = _('Name:           %(title)s %(firstname)s %(lastname)s\n'
                    'Address:        %(street)s\n'
                    '                %(country)s, %(postcode)s %(town)s\n'
                    'POB:            %(postbox)s\n'
                    'E-Mail:         %(email)s\n'
                    'Phone:          %(phone)s\n'
                    'Mobile:         %(mobile)s\n'
                    'Date of birth:  %(birthdate)s\n'
                    'Tags:           %(tags)s\n')
            self._long_entry_format = msg
        return self._long_entry_format

    @property
    def short_entry_format(self):
        if not self._short_entry_format:
            _ = self.translation.ugettext
            msg = _('%(firstname)s %(lastname)s')
            self._short_entry_format = msg
        return self._short_entry_format



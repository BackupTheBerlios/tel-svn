#!/usr/bin/env python
# -*- coding: utf-8 -*-
# application distutils
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
# DEALINGS IN THE SOFTWARE."""

"""Distutils extension to install applications, including support for
gettext catalogs, application data and manpages"""


import os
from glob import glob
from string import Template

from distutils import core
from distutils import dist
from distutils import dir_util
from distutils import spawn
from distutils import util
from distutils import filelist

from distutils.dist import Distribution
from distutils.cmd import Command, install_misc
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.clean import clean
from distutils.command.install_data import install_data
from distutils.command.install_lib import install_lib


PO_DIRECTORY = 'po'
INSTALL_LOG = 'installed_files'

def setup(**kwargs):
    if 'cmdclass' not in kwargs:
        kwargs['cmdclass'] = {}

    cmdclasses = {
        'messages': Messages,
        'build_messages': BuildMessages,
#        'build_manpages': BuildManPages,
        'build': AppBuild,
        'install_links': InstallLinks,
        'install_app_modules': InstallAppModules,
        'install_app_data': InstallAppData,
        'install_messages': InstallMessages,
#        'install_manpages': InstallManPages,
        'configure': Configure,
        'install': AppInstall,
        'uninstall': Uninstall,
        'clean': AppClean
        }

    for key in cmdclasses:
        kwargs['cmdclass'].setdefault(key, cmdclasses[key])

    kwargs.setdefault('distclass', AppDistribution)

    core.setup(**kwargs)


def has_messages(self):
    return bool(self.distribution.po)


def has_app_data(self):
    return bool(self.distribution.appdata)


def has_app_modules(self):
    return bool(self.distribution.appmodules)


def has_links(self):
    return bool(self.distribution.links)


def is_configurable(self):
    return bool(self.distribution.configurable)


class AppDistribution(Distribution):
    """:ivar po: A list of all source files, which contains messages"""
    def __init__(self, attrs):
        self.po = None
        self.appdata = None
        self.appmodules = None
        self.links = None
        self.configurable = None
        Distribution.__init__(self, attrs)


class Messages(Command):
    description = 'Extract messages from source files'

    user_options = [('xgettext-exe=', None,
                     'Full path to the xgetext executable'),
                    ('msgmerge-exe=', None,
                     'Full path to the msgmerge executable')]

    def initialize_options(self):
        self.xgettext_exe = None
        self.msgmerge_exe = None

    def finalize_options(self):
        if self.xgettext_exe is None:
            self.announce('Searching xgettext...')
            self.xgettext_exe = spawn.find_executable('xgettext')
            if self.xgettext_exe is None:
                raise SystemExit('Couldn\'t find "xgettext".')
            self.announce('  ...xgettext found at %s' % self.xgettext_exe)

        if self.msgmerge_exe is None:
            self.announce('Searching msgmerge...')
            self.msgmerge_exe = spawn.find_executable('msgmerge')
            if self.msgmerge_exe is None:
                raise SystemExit('Couldn\'t find "msgmerge".')
            self.announce('  ...msgmerge found at %s' % self.msgmerge_exe)

    def run(self):
        if not os.path.exists(PO_DIRECTORY):
            os.mkdir(PO_DIRECTORY)
        name = self.distribution.get_name() + '.pot'
        target = os.path.join(PO_DIRECTORY, name)
        cmd = [self.xgettext_exe, '-o', target]
        cmd.extend(self.distribution.po)
        self.spawn(cmd)

        for po_file in glob(os.path.join(PO_DIRECTORY, '*.po')):
            cmd = [self.msgmerge_exe, '-q', '-o', po_file, po_file, target]
            self.spawn(cmd)


class BuildMessages(Command):
    description = 'Compile message catalogs'

    user_options = [('build-dir=', 'd',
                     'directory to build message catalogs in'),
                    ('msgfmt-exe=', None, 'Path to the msgfmt executable')]

    def initialize_options(self):
        self.build_dir = None
        self.msgfmt_exe = None

    def finalize_options(self):
        self.set_undefined_options('build', ('msgfmt_exe', 'msgfmt_exe'),
                                   ('build_messages', 'build_dir'))

    def run(self):
        self.announce('Building po catalogs...')
        self.mkpath(self.build_dir)

        po_files = os.path.join('po', '*.po')
        po_files = glob(po_files)
        for po_file in po_files:
            language = os.path.splitext(os.path.basename(po_file))[0]
            self.announce('Building catalog %s...' % language)
            target = os.path.join(self.build_dir, language + '.gmo')
            cmd = [self.msgfmt_exe, '-o', target, po_file]
            self.spawn(cmd)
        self.announce('Done building message catalogs.')


class Configure(Command):
    description = 'Configure files'

    user_options = [('build-dir=', 'd',
                     'directory to put configured files in')]

    def initialize_options(self):
        self.build_dir = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_configure', 'build_dir'))

    def read_template(self, fso):
        """Reads template from `fso`"""
        stream = open(fso)
        template = Template(stream.read())
        stream.close()
        return template

    def write_substituted(self, target, template, mapping=None, **kwargs):
        """Substitudes `template` with `**kwargs` and `mapping` and writes
        it to `target`"""
        substituted = template.safe_substitute(mapping, **kwargs)
        stream = open(target, 'w')
        stream.write(substituted)
        stream.close()


    def run(self):
        self.announce('Configuring files...')
        self.mkpath(self.build_dir)
        install = self.get_finalized_command('install')

        for fso in self.distribution.configurable:
            target = os.path.join(self.build_dir, fso)
            target_dir = os.path.dirname(target)
            self.mkpath(target_dir)
            template = self.read_template(fso)
            self.write_substituted(target, template, vars(install))
            self.announce('%s configured' % fso)


class AppBuild(build):
    user_options = build.user_options[:]
    user_options.extend([
        ('build-messages=', None, 'Build directory for messages'),
        ('build-configure=', None, 'Directory for configured files'),
        ('msgfmt-exe=', None, 'Path to the msgfmt executable')])

    sub_commands = build.sub_commands[:]
    sub_commands.extend([
        ('build_messages', has_messages),
        ('configure', is_configurable)])

    def initialize_options(self):
        self.build_messages = None
        self.build_configure = None
        self.msgfmt_exe = None
        build.initialize_options(self)

    def finalize_options(self):
        if self.build_messages is None:
            self.build_messages = os.path.join(self.build_base,
                                               'po')

        if self.build_configure is None:
            self.build_configure = os.path.join(self.build_base,
                                                'config')

        if self.msgfmt_exe is None:
            self.announce('Searching msgfmt...')
            self.msgfmt_exe = spawn.find_executable('msgfmt')
            if self.msgfmt_exe is None:
                raise SystemExit('Couldn\'t find "msgfmt".')
            self.announce('  ...msgfmt found at %s' % self.msgfmt_exe)

        build.finalize_options(self)


class InstallStuff(install_misc):
    """Base class for some install commands"""
    def mkpath (self, name, mode=0777):
        return dir_util.mkpath(name, mode, dry_run=self.dry_run)


class InstallMessages(InstallStuff):
    description = 'Installs message catalogs'

    user_options = install_misc.user_options[:]
    user_options.append(('build-dir=', 'b',
                         'build directory (where to install from)'))
    user_options.append(('skip-build', None, "skip the build steps"))

    boolean_options = ['skip-build']

    def initialize_options(self):
        self.install_dir = None
        self.build_dir = None
        self.skip_build = None
        install_misc.initialize_options(self)

    def finalize_options(self):
        self._install_dir_from('install_messages')
        self.set_undefined_options('build', ('build_messages', 'build_dir'))
        self.set_undefined_options('install', ('skip_build', 'skip_build'))

    def run(self):
        if not self.skip_build:
            self.run_command('build_messages')
        self.announce('Installing message catalogs...')
        po_files = glob(os.path.join(self.build_dir, '*.gmo'))
        for po_file in po_files:
            language = os.path.splitext(os.path.basename(po_file))[0]
            target_dir = os.path.join(self.install_dir, language,
                                      'LC_MESSAGES')
            self.outfiles.extend(self.mkpath(target_dir))
            target = os.path.join(target_dir,
                                  self.distribution.get_name() + '.mo')
            self.copy_file(po_file, target)
            self.outfiles.append(target)


class InstallAppModules(install_lib):
    description = 'Install python modules'

    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('install_app_modules', 'install_dir'))
        install_lib.finalize_options(self)
        self.modules = self.distribution.appmodules
        self.configurable = self.distribution.configurable
        self.outfiles = []

    def run(self):
        if not os.path.exists(self.install_dir):
            self.outfiles.extend(self.mkpath(self.install_dir))

        build = self.get_finalized_command('build')
        build_configure = build.build_configure
        for item in self.modules:
            if os.path.isfile(item):
                if item in self.configurable:
                    item = os.path.join(build_configure, item)
                target, copied = self.copy_file(item, self.install_dir)
                self.outfiles.append(target)
            elif os.path.isdir(item):
                # FIXME: respect "configureable" files
                files.extend(filelist.findall(item))
            else:
                self.warn('Unable to find %s...' % item)

        self.byte_compile(self.outfiles)
        self.outfiles.extend(self._bytecode_filenames(self.outfiles))

    def get_outputs(self):
        return self.outfiles

    def mkpath (self, name, mode=0777):
        return dir_util.mkpath(name, mode, dry_run=self.dry_run)


class InstallAppData(install_data):
    description = 'Install application data'

    def initialize_options(self):
        install_data.initialize_options(self)

    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('install_app_data', 'install_dir'))
        install_data.finalize_options(self)
        self.appdata = self.distribution.appdata

    def run(self):
        if not os.path.exists(self.install_dir):
            self.outfiles.extend(self.mkpath(self.install_dir))

        for item in self.appdata:
            if isinstance(item, basestring):
                # put it right into the installation directory
                if os.path.isfile(item):
                    (f, copied) = self.copy_file(item, self.install_dir)
                    self.outfiles.append(f)
                elif os.path.isdir(item):
                    target =  os.path.join(self.install_dir, item)
                    files = self.copy_tree(item, target)
                    self.outfiles.extend(files)
                else:
                    self.warn('Unable to find %s...' % item)
            else:
                # assume we have a tupel-like thing here. target directory
                # relative to install_dir is in first element
                target_dir = item[0]
                if self.root:
                    target_dir = util.change_root(self.root, target_dir)
                else:
                    target_dir = os.path.join(self.install_dir, target_dir)

                for fso in item[1]:
                    if os.path.isdir(fso):
                        files = self.copy_tree(fso, target_dir)
                        self.outfiles.extend(files)
                    elif os.path.isfile(fso):
                        (f, copied) = self.copy_file(fso, target_dir)
                        self.outfiles.append(f)
                    else:
                        self.warn('Unable to find %s...' % fso)

    def mkpath (self, name, mode=0777):
        return dir_util.mkpath(name, mode, dry_run=self.dry_run)


class InstallLinks(InstallStuff):
    description = ('Installs executable links to scripts in application '
                   'lib directory')

    user_options = install_misc.user_options[:]

    def finalize_options(self):
        self._install_dir_from('install_links')

    def run(self):
        appmodules = self.get_finalized_command('install_app_modules')

        target_directory = appmodules.install_dir

        if not os.path.exists(self.install_dir):
            self.outfiles.extend(self.mkpath(self.install_dir))

        for link in self.distribution.links:
            dest = os.path.join(self.install_dir, link[0])
            target = os.path.join(target_directory, link[1])
            # make sure, target is executable (link would be vain otherwise)
            mode = int('755', 8)
            self.announce('Changing mode of %s to %o' % (target, mode))
            os.chmod(target, mode)
            self.announce('linking %s to %s' % (dest, target))
            if not self.dry_run:
                if os.path.islink(dest):
                    os.remove(dest)
                os.symlink(target, dest)
                self.outfiles.append(dest)


class AppInstall(install):
    user_options = install.user_options[:]
    user_options.extend([
        ('install-messages=', None,
         'Installation directory of message catalogs'),
        ('install-app-data=', None,
         'Installation directory for application data'),
        ('install-app-modules=', None,
         'Installation directory for application modules'),
        ('install-links=', None,
         'Installation directory for executable links')])

    sub_commands = install.sub_commands[:]
    sub_commands.extend([
        ('install_messages', has_messages),
        ('install_app_data', has_app_data),
        ('install_app_modules', has_app_modules),
        ('install_links', has_links)])

    def initialize_options(self):
        self.install_messages = None
        self.install_app_data = None
        self.install_app_modules = None
        self.install_links = None
        install.initialize_options(self)

    def finalize_options(self):
        install.finalize_options(self)
        name = self.distribution.get_name()
        if self.install_messages is None:
            self.install_messages = os.path.join(self.install_data, 'share',
                                                 'locale')
        if self.install_app_data is None:
            self.install_app_data = os.path.join(self.install_data, 'share',
                                                 name)

        if self.install_app_modules is None:
            self.install_app_modules = os.path.join(self.install_data,
                                                    'lib', name)


        if self.install_links is None:
            self.install_links = self.install_scripts

    def run(self):
        install.run(self)
        stream = open(INSTALL_LOG, 'w')
        outputs = self.get_outputs()
        stream.write('\n'.join(outputs))
        stream.write('\n')
        stream.close()


class Uninstall(Command):
    description = 'Whipes tel from this computer'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if not os.path.isfile(INSTALL_LOG):
            msg = 'Cannot find the list file "%s".' % INSTALL_LOG
            raise SystemExit(msg)

        stream = open(INSTALL_LOG)
        files = stream.readlines()
        stream.close()

        # sort and reverse the file list. This puts the directories after
        # the files
        files.sort()
        files.reverse()

        for fso in files:
            fso = fso.strip()
            self.announce('Removing %s...')
            try:
                if not self.dry_run:
                    if os.path.isfile(fso) or os.path.islink(fso):
                        os.remove(fso)
                    elif os.path.isdir(fso):
                        os.rmdir(fso)
            except OSError, e:
                self.warn('Could not remove %s: %s' % (fso, e))


class AppClean(clean):
    user_options = clean.user_options[:]
    user_options.extend([
        ('build-messages=', None, 'Build directory for messages'),
        ('build-configure=', None, 'Directory for configured files')])

    def initialize_options(self):
        self.build_messages = None
        self.build_configure = None
        clean.initialize_options(self)

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_messages', 'build_messages'),
                                   ('build_configure', 'build_configure'))
        clean.finalize_options(self)

    def run(self):
        if self.all:
            for directory in (self.build_configure, self.build_messages):
                if os.path.exists(directory):
                    dir_util.remove_tree(directory)
            else:
                self.warn("'%s' does not exist -- can't clean it" %
                          directory)
        clean.run(self)

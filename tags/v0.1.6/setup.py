#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tel install script
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


import os
from glob import glob

from distutils.core import setup
from distutils.core import Distribution
from distutils import log
from distutils import dir_util
from distutils import spawn
from distutils import util

from distutils.cmd import Command
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.clean import clean
from distutils.command.install_data import install_data


PO_DIRECTORY = 'po'


def has_messages(self):
    return bool(self.distribution.po)


def has_app_data(self):
    return bool(self.distribution.appdata)


def has_links(self):
    return bool(self.distribution.links)


class TelDistribution(Distribution):
    """:ivar po: A list of all source files, which contains messages"""
    def __init__(self, attrs):
        self.po = None
        self.appdata = None
        self.links = None
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
        self.set_undefined_options('build', ('msgfmt_exe', 'msgfmt_exe'))
        self.set_undefined_options('build', ('build_messages', 'build_dir'))

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


class ExtendedBuild(build):
    user_options = build.user_options[:]
    user_options.append(('build-messages=', None,
         "build directory for messages"))
    user_options.append(('msgfmt-exe=', None,
                         'Path to the msgfmt executable'))

    sub_commands = build.sub_commands[:]
    sub_commands.append(('build_messages', has_messages))

    def get_command_name(self):
        return 'build'
   
    def initialize_options(self):
        self.build_messages = None
        self.msgfmt_exe = None
        build.initialize_options(self)

    def finalize_options(self):
        if self.build_messages is None:
            self.build_messages = os.path.join(self.build_base,
                                               'po')
        if self.msgfmt_exe is None:
            self.announce('Searching msgfmt...')
            self.msgfmt_exe = spawn.find_executable('msgfmt')
            if self.msgfmt_exe is None:
                raise SystemExit('Couldn\'t find "msgfmt".')
            self.announce('  ...msgfmt found at %s' % self.msgfmt_exe)
        build.finalize_options(self)
            

class InstallMessages(Command):
    description = 'Installs message catalogs'

    user_options = [
        ('install-dir=', 'd', "directory to install messages to"),
        ('root=', None, 'alternative root directory'),
        ('build-dir=','b', "build directory (where to install from)"),
        ('skip-build', None, "skip the build steps")]

    boolean_options = ['skip-build']

    def initialize_options(self):
        self.install_dir = None
        self.build_dir = None
        self.skip_build = None

    def finalize_options(self):
        self.set_undefined_options('build', ('build_messages', 'build_dir'))
        self.set_undefined_options('install',
                                   ('install_messages', 'install_dir'),
                                   ('force', 'force'),
                                   ('skip_build', 'skip_build'))

    def run(self):
        if not self.skip_build:
            self.run_command('build_messages')
        self.announce('Installing message catalogs...')
        po_files = glob(os.path.join(self.build_dir, '*.gmo'))
        for po_file in po_files:
            language = os.path.splitext(os.path.basename(po_file))[0]
            target_dir = os.path.join(self.install_dir, language,
                                      'LC_MESSAGES')
            self.mkpath(target_dir)
            target = os.path.join(target_dir,
                                  self.distribution.get_name() + '.mo')
            self.copy_file(po_file, target)


class InstallAppData(install_data):
    def initialize_options(self):
        install_data.initialize_options(self)

    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('install_app_data', 'install_dir'))
        install_data.finalize_options(self)
        self.appdata = self.distribution.appdata

    def run(self):
        self.mkpath(self.install_dir)
        # used for byte compiling
        created_files = []

        for item in self.appdata:
            if isinstance(item, basestring):
                # put it right into the installation directory
                if os.path.isfile(item):
                    (f, copied) = self.copy_file(item, self.install_dir)
                    created_files.append(f)
                elif os.path.isdir(item):
                    target =  os.path.join(self.install_dir, item)
                    files = self.copy_tree(item, target)
                    created_files.extend(files)
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
                        created_files.extend(files)
                    elif os.path.isfile(fso):
                        (f, copied) = self.copy_file(fso, target_dir)
                        created_files.append(f)
                    else:
                        self.warn('Unable to find %s...' % fso)
                        
        # byte compilation
        util.byte_compile(created_files, optimize=0, force=True,
                          dry_run=self.dry_run)


class InstallLinks(Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass
    
    def run(self):
        scripts = self.get_finalized_command('install_scripts')
        appdata = self.get_finalized_command('install_app_data')

        target_dir = appdata.install_dir
        link_dir = scripts.install_dir

        if not os.path.exists(link_dir):
            self.mkpath(link_dir)

        for link in self.distribution.links:
            dest = os.path.join(link_dir, link[0])
            target = os.path.join(target_dir, link[1])
            # make sure, target is executable (link would be vain otherwise)
            mode = int('755', 8)
            self.announce('Changing mode of %s to %o' % (target, mode))
            os.chmod(target, mode)
            self.announce('linking %s to %s' % (dest, target))
            if not self.dry_run:
                if os.path.islink(dest):
                    os.remove(dest)
                os.symlink(target, dest)
                    

class ExtendedInstall(install):
    user_options = install.user_options[:]
    user_options.append(('install-messages=', None,
                         'Installation directory of message catalogs'))
    user_options.append(('install-app-data=', None,
                         'Installation directory for application data'))

    sub_commands = install.sub_commands[:]
    sub_commands.append(('install_messages', has_messages))
    sub_commands.append(('install_app_data', has_app_data))
    sub_commands.append(('install_links', has_links))

    def initialize_options(self):
        self.install_messages = None
        self.install_app_data = None
        install.initialize_options(self)

    def finalize_options(self):
        install.finalize_options(self)
        if self.install_messages is None:
            self.install_messages = os.path.join(self.install_data, 'share',
                                                 'locale')
        if self.install_app_data is None:
            name = self.distribution.get_name()
            self.install_app_data = os.path.join(self.install_data, 'share',
                                                 name)


class ExtendedClean(clean):
    user_options = clean.user_options[:]
    user_options.append(('build-messages=', None,
                         'build directory for messages'))

    def initialize_options(self):
        self.build_messages = None
        clean.initialize_options(self)

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_messages', 'build_messages'))
        clean.finalize_options(self)

    def run(self):
        if self.all:
            if os.path.exists(self.build_messages):
                dir_util.remove_tree(self.build_messages)
            else:
                self.warn("'%s' does not exist -- can't clean it",
                          self.build_messages)
        clean.run(self)
        

def get_version():
    filename = 'tel.py'
    stream = open(filename)
    for line in stream:
        if line.startswith('__version__'):
            stream.close()
            exec line
            return __version__
        elif line.startswith('import'):
            raise SystemExit('Couldn\'t extract version information')
        

long_description = """\
tel is a little console-based phone book program. It allows adding,
modifing, editing and searching of phone book entries right on your
terminal. Pretty printing capabilites are also provided.
Entries are stored in simple csv file. This eases import and export with
common spread sheet applications like Microsoft Excel or OpenOffice.org
Calc."""


setup(name='tel',
      version=get_version(),
      description='A little terminal phone book',
      long_description=long_description,
      author='Sebastian \'lunar\' Wiesner',
      author_email='basti.wiesner@gmx.net',
      url='http://tel.berlios.de',
      license='MIT/X11',
      links=[('tel', 'tel.py')],
      po=['tel.py'],
      appdata=['tel.py'],
      distclass=TelDistribution,
      cmdclass={'messages': Messages,
                'build_messages': BuildMessages,
                'build': ExtendedBuild,
                'install_messages': InstallMessages,
                'install_links': InstallLinks,
                'install_app_data': InstallAppData,
                'install': ExtendedInstall,
                'clean': ExtendedClean}
      )

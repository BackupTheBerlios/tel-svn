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

from distutils.cmd import Command, install_misc
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.clean import clean
from distutils.command.install_data import install_data


PO_DIRECTORY = 'po'
INSTALL_LOG = 'installed_files'


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
            

class InstallMessages(install_misc):
    description = 'Installs message catalogs'

    user_options = install_misc.user_options[:]
    user_options.append(('build-dir=','b',
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
            self.mkpath(target_dir)
            target = os.path.join(target_dir,
                                  self.distribution.get_name() + '.mo')
            self.copy_file(po_file, target)
            self.outfiles.append(target)


class InstallAppData(install_data):
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

        # FIXME: respect --no-compile here
        # byte compilation
        util.byte_compile(self.outfiles, optimize=0, force=True,
                          dry_run=self.dry_run)
        # extend outfiles with compiled files
        python_sources = filter(lambda f: f.endswith('.py'), self.outfiles)
        compiled = map(lambda f: f+'c', python_sources)
        self.outfiles.extend(compiled)

    def mkpath (self, name, mode=0777):
        return dir_util.mkpath(name, mode, dry_run=self.dry_run)


class InstallLinks(install_misc):
    description = ('Installs executable links to scripts in application '
                   'data directory')

    user_options = install_misc.user_options[:]

    def finalize_options(self):
        self._install_dir_from('install_links')
    
    def run(self):
        appdata = self.get_finalized_command('install_app_data')

        target_directory = appdata.install_dir

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

    def mkpath (self, name, mode=0777):
        return dir_util.mkpath(name, mode, dry_run=self.dry_run)
                    

class ExtendedInstall(install):
    user_options = install.user_options[:]
    user_options.append(('install-messages=', None,
                         'Installation directory of message catalogs'))
    user_options.append(('install-app-data=', None,
                         'Installation directory for application data'))
    user_options.append(('install-links=', None,
                         'Installation directory for executable links'))

    sub_commands = install.sub_commands[:]
    sub_commands.append(('install_messages', has_messages))
    sub_commands.append(('install_app_data', has_app_data))
    sub_commands.append(('install_links', has_links))

    def initialize_options(self):
        self.install_messages = None
        self.install_app_data = None
        self.install_links = None
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


import optparse
# get the real source file, not the compiled one
optparse_source = optparse.__file__.rstrip('c')


setup(name='tel',
      version=get_version(),
      description='A little terminal phone book',
      long_description=long_description,
      author='Sebastian \'lunar\' Wiesner',
      author_email='basti.wiesner@gmx.net',
      url='http://tel.berlios.de',
      license='MIT/X11',
      links=[('tel', 'tel.py')],
      po=['tel.py', optparse_source],
      appdata=['tel.py'],
      distclass=TelDistribution,
      cmdclass={'messages': Messages,
                'build_messages': BuildMessages,
                'build': ExtendedBuild,
                'install_messages': InstallMessages,
                'install_links': InstallLinks,
                'install_app_data': InstallAppData,
                'install': ExtendedInstall,
                'clean': ExtendedClean,
                'uninstall': Uninstall}
      )

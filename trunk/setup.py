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


from distutils.core import setup
from distutils.core import Distribution
from distutils import log
from distutils.cmd import Command
from distutils.dir_util import remove_tree
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.clean import clean as _clean
from distutils.command.install_data import install_data
from distutils.spawn import find_executable

import os
from glob import glob


PO_DIRECTORY = 'po'

# TODO: add links command to create executable symlinks

def has_messages(self):
    return bool(self.distribution.po)

def has_application_data(self):
    return bool(self.distribution.appdata)


class TelDistribution(Distribution):
    """:ivar po: A list of all source files, which contains messages"""
    def __init__(self, attrs):
        self.po = None
        self.appdata = None
        Distribution.__init__(self, attrs)


class Messages(Command):
    description = 'Extract messages from source files'

    user_options = [('xgettext-exe=', None,
                     'Full path to the xgetext executable'),
                    ('msgmerge-exe=', None,
                     'Full path to the msgmerge executable')]

    def get_command_name(self):
        return 'messages'

    def initialize_options(self):
        self.xgettext_exe = None
        self.msgmerge_exe = None

    def finalize_options(self):
        if self.xgettext_exe is None:
            self.announce('Searching xgettext...')
            self.xgettext_exe = find_executable('xgettext')
            if self.xgettext_exe is None:
                raise SystemExit('Couldn\'t find "xgettext".')
            self.announce('  ...xgettext found at %s' % self.xgettext_exe)

        if self.msgmerge_exe is None:
            self.announce('Searching msgmerge...')
            self.msgmerge_exe = find_executable('msgmerge')
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
            cmd = [self.msgmerge_exe, '-q', '-o', po_file, po_file]
            self.spawn(cmd)            
        

class BuildMessages(Command):
    description = 'Compile message catalogs'

    user_options = [('build-dir=', 'd',
                     'directory to build message catalogs in'),
                    ('msgfmt-exe=', None, 'Path to the msgfmt executable')]

    def get_command_name(self):
        return 'build_messages'

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
            self.msgfmt_exe = find_executable('msgfmt')
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

    def get_command_name(self):
        return 'install_messages'

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
            self.mkpath(target_dir, dry_run=self.dry_run)
            target = os.path.join(target_dir,
                                  self.distribution.get_name() + '.mo')
            self.copy_file(po_file, target)


class InstallAppData(install_data):
    def get_command_name(self):
        return 'install_app_data'

    def initialize_options(self):
        install_data.initialize_options(self)

    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('install_app_data', 'install_dir',
                                    'root', 'root',
                                    'force', 'force'))
        self.appdata = self.distribution.appdata

    def run(self):
        self.mkpath(self.install_dir)
        for item in self.appdata:
            if isinstance(item, basestring):
                # put it right into the installation directory
                if os.path.isfile(item):
                    self.copy_file(item, self.install_dir)
                elif os.path.isdir(item):
                    self.copy_tree(item, os.path.join(self.install_dir,
                                                      item))
                else:
                    self.warn('Unable to find %s...' % item)
            else:
                # assume we have a tupel-like thing here. target directory
                # relative to install_dir is in first element
                target_directory = item[0]
    # FIXME: continue implementation here


class ExtendedInstall(install):
    user_options = install.user_options[:]
    user_options.append(('install-messages=', None,
                         'Installation directory of message catalogs'))

    sub_commands = install.sub_commands[:]
    sub_commands.append(('install_messages', has_messages))

    def initialize_options(self):
        self.install_messages = None
        install.initialize_options(self)

    def finalize_options(self):
        install.finalize_options(self)
        if self.install_messages is None:
            self.install_messages = os.path.join(self.install_data, 'share',
                                                 'locale')


class clean(_clean):
    # FIXME: clean up code
    _clean.user_options.append(('build-messages=', None,
                                "build directory for messages (default: 'build.build-messages')"))

    def initialize_options(self):
        _clean.initialize_options(self)
        self.build_messages = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_lib', 'build_lib'),
                                   ('build_scripts', 'build_scripts'),
                                   ('build_temp', 'build_temp'),
                                   ('build_messages', 'build_messages'))
        self.set_undefined_options('bdist', ('bdist_base', 'bdist_base'))
    def run(self):
        # remove the build/temp.<plat> directory (unless it's already
        # gone)
        if os.path.exists(self.build_temp):
            remove_tree(self.build_temp, dry_run=self.dry_run)
        else:
            log.debug("'%s' does not exist -- can't clean it",
                      self.build_temp)

        if self.all:
            # remove build directories
            for directory in (self.build_lib,
                              self.bdist_base,
                              self.build_scripts,
                              self.build_messages):
                if os.path.exists(directory):
                    remove_tree(directory, dry_run=self.dry_run)
                else:
                    log.warn("'%s' does not exist -- can't clean it",
                             directory)

        # just for the heck of it, try to remove the base build directory:
        # we might have emptied it right now, but if not we don't care
        if not self.dry_run:
            try:
                os.rmdir(self.build_base)
                log.info("removing '%s'", self.build_base)
            except OSError:
                pass

# FIXME: of course the right things should be here
setup(name='tel',
      version='0.0.0.0',
      description='not really relevant',
      long_description='not really relevant',
      author='Zaphod',
      author_email='zaphod@example.com',
      license='GPL',
      platforms='what',
      scripts=['foo'],
      po=['tel.py'],
      appdata=['tel.py'],
      distclass=TelDistribution,
      cmdclass={'messages': Messages,
                'build_messages': BuildMessages,
                'build': ExtendedBuild,
                'install_messages': InstallMessages,
                'install': ExtendedInstall,
                'clean': clean}
      )

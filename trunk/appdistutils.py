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
# THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE."""

"""Distutils extension to install applications, including support for
gettext catalogs, uninstallation support, extended script installation
and improved source distribution generation."""

from __future__ import with_statement

import os
import sys
from glob import glob
from itertools import ifilter

from distutils import core
from distutils import util
from distutils import spawn
from distutils import log
from distutils import dep_util

from distutils.dist import Distribution
from distutils.cmd import Command, install_misc
from distutils.command import build_scripts
from distutils.command.sdist import sdist
from distutils.command.build import build
from distutils.command.install import install, INSTALL_SCHEMES
from distutils.command.install_lib import install_lib



# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']


INSTALL_LOG = 'install.log'


def setup(**kwargs):
    if 'cmdclass' not in kwargs:
        kwargs['cmdclass'] = {}

    cmdclasses = {
        'messages': Messages,
        'sdist': SDist,
        'build_messages': BuildMessages,
        'build_scripts': BuildScripts,
#        'build_manpages': BuildManPages,
        'build': AppBuild,
#        'install_manpages': InstallManPages,
        'install_lib': InstallLib,
        'install': AppInstall,
        'uninstall': Uninstall,
        }

    for key in cmdclasses:
        kwargs['cmdclass'].setdefault(key, cmdclasses[key])

    kwargs.setdefault('distclass', AppDistribution)

    core.setup(**kwargs)


def has_messages(self):
    return bool(self.distribution.po)


class AppDistribution(Distribution):
    def __init__(self, attrs):
        self.po = None
        self.po_dir = None
        Distribution.__init__(self, attrs)

    def has_messages(self):
        return bool(self.po)


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
        for name in self.distribution.po:
            target_dir = os.path.join(self.distribution.po_dir, name)
            self.mkpath(target_dir)
            catalog_file = os.path.join(target_dir, name + '.pot')
            cmd = [self.xgettext_exe, '-o', catalog_file]
            cmd.extend(self.distribution.po[name])
            self.spawn(cmd)
            for po_file in glob(os.path.join(target_dir, '*.po')):
                cmd = [self.msgmerge_exe, '-q', '-o', po_file, po_file,
                       catalog_file]
                self.spawn(cmd)


class SDist(sdist):
    """sdist implementation which is aware of message files"""
    def add_defaults(self):
        """Add all the default files to self.filelist:
          - README or README.txt
          - setup.py
          - test/test*.py
          - all pure Python modules mentioned in setup script
          - all C sources listed as part of extensions or C libraries
            in the setup script (doesn't catch C headers!)
          - all gettext message files
        Warns if (README or README.txt) or setup.py are missing; everything
        else is optional."""
        sdist.add_defaults(self)

        # get the relative pathname of this module
        appdistutils = __file__.rstrip('c')
        prefix = os.path.commonprefix((os.getcwd(), appdistutils))
        appdistutils = appdistutils[len(prefix  + os.sep):]
        # include this module and some extra metadata files, which are
        # standard for applications
        standards = (appdistutils, 'INSTALL', 'COPYING', 'ChangeLog')
        for fn in standards:
            if os.path.exists(fn):
                self.filelist.append(fn)
            else:
                self.warn("standard file '%s' not found" % fn)
        # some optional metadata files, not bad, if they are missing
        optional = ('AUTHORS', 'THANKSTO', 'TODO')
        for fn in ifilter(os.path.exists, optional):
            self.filelist.append(fn)
        # include message files
        if self.distribution.has_messages():
            build_messages = self.get_finalized_command('build_messages')
            self.filelist.extend(build_messages.get_source_files())
        # include package data
        if self.distribution.has_pure_modules():
            build_py = self.get_finalized_command('build_py')
            for pkg, src_dir, build_dir, filenames in build_py.data_files:
                files = (os.path.join(src_dir, filename) for filename in
                         filenames)
                self.filelist.extend(files)


class BuildMessages(Command):
    description = 'Compile message catalogs'

    user_options = [('build-lib=', 'd',
                     'directory to build message catalogs in'),
                    ('msgfmt-exe=', None, 'Path to the msgfmt executable')]

    def initialize_options(self):
        self.build_lib = None
        self.msgfmt_exe = None

    def finalize_options(self):
        # locale data is installed as package data, so we have to use the
        # build_lib directory.
        # This way installation is done automatically by install_lib,
        # we just have to build the message files in the right place.
        self.set_undefined_options('build', ('msgfmt_exe', 'msgfmt_exe'),
                                   ('build_lib', 'build_lib'))

    def _po_packages(self):
        """Returns an informative dict about every po packages specified
        in setup"""
        for name in self.distribution.po:
            source_dir = os.path.join(self.distribution.po_dir, name)
            build_dir = os.path.join(self.build_lib, name, 'locale')
            template = os.path.join(source_dir, name + '.pot')
            pkg = {'name': name,
                   'template': template,
                   'source_dir': source_dir,
                   'build_dir': build_dir}
            yield pkg

    def _po_package_contents(self, package):
        """Returns an informative dictionary about every source po file
        in po `package`"""
        po_files = glob(os.path.join(package['source_dir'], '*.po'))
        for po_file in po_files:
            language = os.path.splitext(os.path.basename(po_file))[0]
            lang_dir = os.path.join(package['build_dir'], language)
            msg_dir = os.path.join(lang_dir, 'LC_MESSAGES')
            mo_file = os.path.join(msg_dir, package['name'] + '.mo')
            yield {'language': language,
                   'lang_dir': lang_dir,
                   'msg_dir': msg_dir,
                   'mo_file': mo_file,
                   'po_file': po_file}

    def run(self):
        self.announce('Building message files...')
        for pkg in self._po_packages():
            self.announce('Building message files for "%(name)s" package...' %
                          pkg)
            for item in self._po_package_contents(pkg):
                self.announce('Building %(language)s...' % item)
                self.mkpath(item['msg_dir'])
                cmd = (self.msgfmt_exe, '-o', item['mo_file'],
                       item['po_file'])
                self.spawn(cmd)
        self.announce('Done building message catalogs.')

    def get_source_files(self):
        """Returns a list of source files for sdist"""
        files = []
        for pkg in self._po_packages():
            files.append(pkg['template'])
            files.extend((item['po_file'] for item in
                          self._po_package_contents(pkg)))
        return files

    def get_outputs(self):
        """Returns a list of files, which are created by this command"""
        outputs = []
        for pkg in self._po_packages():
            outputs.append(pkg['build_dir'])
            for item in self._po_package_contents(pkg):
                outputs.append(item['lang_dir'])
                outputs.append(item['msg_dir'])
                outputs.append(item['mo_file'])
        return outputs


class BuildScripts(build_scripts.build_scripts):
    """Improved install_scripts implementation, which can install scripts
    under different names"""

    def get_source_files(self):
        """Returns a list of source files for sdist"""
        return zip(*self.distribution.scripts)[0]

    def copy_scripts (self):
        """Copy each script listed in 'self.scripts'; if it's marked as a
        Python script in the Unix way (first line matches 'first_line_re',
        ie. starts with "\#!" and contains "python"), then adjust the first
        line to refer to the current Python interpreter as we copy.
        """
        self.mkpath(self.build_dir)
        outfiles = []
        for source, scriptname in self.scripts:
            script = util.convert_path(source)
            # skip empty files
            if not os.path.getsize(script):
                self.warn("%s is an empty file (skipping)" % script)
                continue

            if os.name != 'posix' and not scriptname.endswith('.py'):
                # add py extensions on systems, which don't understand
                # shebangs
                scriptname += '.py'
            outfile = os.path.join(self.build_dir, scriptname)
            outfiles.append(outfile)

            if not self.force and not dep_util.newer(script, outfile):
                log.debug("not copying %s (up-to-date)", script)
                continue

            if not self._adjust_shebang(script, outfile):
                # just copy script, if there was no sheband to adjust
                self.copy_file(script, outfile)

    def _adjust_shebang(self, script, outfile):
        """Checks, if `script` has a sheband, adjust it, if necessary, and
        write the result to `outfile`. Returns True, if anything was
        adjusted."""
        # Always open the file, but ignore failures in dry-run mode --
        # that way, we'll get accurate feedback if we can read the
        # script.
        try:
            with open(script, "r") as stream:
                firstline = stream.readline()
                match = build_scripts.first_line_re.match(firstline)
                if match:
                    post_interp = match.group(1) or ''
                    log.info("copying and adjusting %s -> %s", script,
                             self.build_dir)
                    if not self.dry_run:
                        with open(outfile, "w") as outstream:
                            # write script to target file
                            outstream.write("#!%s%s\n" %  (self.executable,
                                                           post_interp))
                            outstream.write(stream.read())
                        return True
        except IOError:
            if not self.dry_run:
                raise
        return False

    def _correct_file_mode(self):
        """Correct file modes of all scripts"""
        if os.name != 'posix':
            return
        for outfile in self.outfiles:
            if self.dry_run:
                log.info("changing mode of %s", outfile)
            else:
                oldmode = os.stat(outfile).st_mode & 07777
                newmode = (oldmode | 0555) & 07777
                if newmode != oldmode:
                    log.info("changing mode of %s from %o to %o",
                             outfile, oldmode, newmode)
                    os.chmod(outfile, newmode)


class AppBuild(build):
    user_options = build.user_options[:]
    user_options.extend([
        ('build-messages=', None, 'Build directory for messages'),
        ('msgfmt-exe=', None, 'Path to the msgfmt executable')])

    sub_commands = build.sub_commands[:]
    sub_commands.append(('build_messages', has_messages))

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


class InstallLib(install_lib):
    """message files aware install_lib implementation"""
    def build(self):
        install_lib.build(self)
        if not self.skip_build:
            self.run_command('build_messages')

    def get_outputs (self):
        outputs = install_lib.get_outputs(self)
        msg_outputs = self._mutate_outputs(self.distribution.has_messages(),
                                           'build_messages', 'build_lib',
                                           self.install_dir)
        return msg_outputs + outputs


class AppInstall(install):
    def run(self):
        install.run(self)
        # write installation log file
        with open(INSTALL_LOG, 'w') as stream:
            outputs = map(os.path.normpath, self.get_outputs())
            stream.write('\n'.join(outputs))
            stream.write('\n')


class Uninstall(Command):
    description = 'Whipes the program from this computer'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if not os.path.isfile(INSTALL_LOG):
            msg = 'Cannot find the installation log file %s.' % INSTALL_LOG
            sys.exit(msg)

        with open(INSTALL_LOG) as stream:
            files = stream.read().splitlines()

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

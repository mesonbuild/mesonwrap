# Copyright 2015 The Meson development team

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import git
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

from mesonwrap import upstream
from mesonwrap.tools import environment


class CheckError(Exception):
    pass


def print_status(msg, check, fatal=True, quiet=False):
    '''Prints msg with success indicator based on check parameter.
    Args:
        msg: str, status message to print
        check: bool, success of the check
        fatal: bool, if exception should be raised
        quiet: bool, if message should be printed on success
    Raises: CheckError(msg) if not check and fatal
    '''
    OK_CHR = '\u2611'
    FAIL_CHR = '\u2612'
    status = OK_CHR if check else FAIL_CHR
    if not quiet or not check:
        print('{msg}: {status}'.format(msg=msg, status=status))
    if not check and fatal:
        raise CheckError(msg)


class Reviewer:

    @staticmethod
    def _get_project(project):
        gh = environment.Github()
        org = gh.get_organization('mesonbuild')
        return org.get_repo(project)

    @classmethod
    def from_pull_request(cls, project, pull_id):
        pull = cls._get_project(project).get_pull(pull_id)
        return cls(project=project, clone_url=pull.head.repo.clone_url,
                   branch=pull.base.ref, source_branch=pull.head.ref)

    @classmethod
    def from_committed(cls, project, branch):
        return cls(project=project,
                   clone_url=cls._get_project(project).clone_url,
                   branch=branch)

    @classmethod
    def from_repository(cls, project, clone_url, branch):
        return cls(project=project, clone_url=clone_url, branch=branch)

    def __init__(self, project, clone_url, branch, source_branch=None):
        self._project = project
        self._clone_url = clone_url
        self._branch = branch
        self._source_branch = source_branch or branch
        self.strict_fileset = True

    def review(self, export_sources=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            r = self.review_int(tmpdir)
            if export_sources:
                shutil.copytree(os.path.join(tmpdir, 'src'), export_sources)
            return r

    def review_int(self, tmpdir):
        head_dir = os.path.join(tmpdir, 'head')
        head_repo = git.Repo.clone_from(self._clone_url, head_dir,
                                        branch=self._source_branch)
        try:
            self.check_basics(head_repo)
            self.check_files(head_dir)
            upwrap = upstream.UpstreamWrap.from_file(
                os.path.join(head_dir, 'upstream.wrap'))
            self.check_wrapformat(upwrap)
            self.check_download(tmpdir, upwrap)
            self.check_extract(tmpdir, upwrap)
            self.check_build(tmpdir, upwrap)
            return True
        except CheckError:
            return False

    @staticmethod
    def check_has_no_path_separators(name, value):
        print_status(name + ' has no path separators',
                     '/' not in value and '\\' not in value)

    def check_wrapformat(self, upwrap):
        print_status('upstream.wrap has directory', upwrap.has_directory)
        self.check_has_no_path_separators('upstream.wrap directory',
                                          upwrap.directory)
        print_status('upstream.wrap has source_url', upwrap.has_source_url)
        print_status('upstream.wrap has source_filename',
                     upwrap.has_source_filename)
        self.check_has_no_path_separators('upstream.wrap source_filename',
                                          upwrap.source_filename)
        print_status('upstream.wrap has source_hash', upwrap.has_source_hash)

    def check_files(self, head_dir):
        found = False
        permitted_files = ['upstream.wrap', 'meson.build', 'readme.txt',
                           'meson_options.txt', '.gitignore', 'LICENSE.build']
        for root, dirs, files in os.walk(head_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            for fname in files:
                if fname not in permitted_files:
                    if not found:
                        print('Non-buildsystem files found:')
                    found = True
                    abs_name = os.path.join(root, fname)
                    rel_name = abs_name[len(head_dir) + 1:]
                    print(' ', rel_name)
        print_status('Repo contains only buildsystem files', not found,
                     fatal=self.strict_fileset)

    @staticmethod
    def isfile(head_dir, filename):
        return os.path.isfile(os.path.join(head_dir, filename))

    def check_basics(self, head_repo):
        print('Inspecting project %s, branch %s.' %
              (self._project, self._branch))
        head_dir = head_repo.working_dir
        print_status('Repo name valid',
                     re.fullmatch('[a-z0-9._]+', self._project))
        print_status('Branch name valid',
                     re.fullmatch('[a-z0-9._]+', self._branch))
        print_status('Target branch is not master', self._branch != 'master')
        print_status('Has readme.txt', self.isfile(head_dir, 'readme.txt'))
        print_status('Has LICENSE.build',
                     self.isfile(head_dir, 'LICENSE.build'))
        print_status('Has upstream.wrap',
                     self.isfile(head_dir, 'upstream.wrap'))
        print_status('Has toplevel meson.build',
                     self.isfile(head_dir, 'meson.build'))

    @staticmethod
    def _fetch(url):
        data = None
        exc = None
        try:
            with urllib.request.urlopen(url) as u:
                data = u.read()
        except Exception as e:
            exc = e
        return (data, exc)

    def check_download(self, tmpdir, upwrap):
        source_data, download_exc = self._fetch(upwrap.source_url)
        try:
            print_status('Download url works', download_exc is None)
        except CheckError:
            print(' error:', str(download_exc))
            raise
        with open(os.path.join(tmpdir, upwrap.source_filename), 'wb') as f:
            f.write(source_data)
        h = hashlib.sha256()
        h.update(source_data)
        calculated_hash = h.hexdigest()
        try:
            print_status('Hash matches', calculated_hash == upwrap.source_hash)
        except CheckError:
            print(' expected:', upwrap.source_hash)
            print('      got:', calculated_hash)
            raise

    @staticmethod
    def mergetree(src, dst, ignore=None):
        for dirpath, dirnames, filenames in os.walk(src):
            prefix = os.path.relpath(dirpath, src)
            dstpath = os.path.join(dst, prefix)
            try:
                del dirnames[dirnames.index('.git')]
            except IndexError:
                pass
            for d in dirnames:
                os.makedirs(os.path.join(dstpath, d), exist_ok=True)
            for f in filenames:
                if f in ('readme.txt', 'upstream.wrap'):
                    continue
                dest = os.path.join(dstpath, f)
                print_status('{!r} already exists'.format(
                                 os.path.join(prefix, f)),
                             not os.path.exists(dest),
                             quiet=True)
                shutil.copy2(os.path.join(dirpath, f), dest)
        return True

    def check_extract(self, tmpdir, upwrap):
        # TODO lead_directory_missing
        srcdir = os.path.join(tmpdir, 'src')
        os.mkdir(srcdir)
        shutil.unpack_archive(os.path.join(tmpdir, upwrap.source_filename),
                              srcdir)
        srcdir = os.path.join(srcdir, upwrap.directory)
        print_status('upstream.wrap directory {!r} exists'.format(
                         upwrap.directory),
                     os.path.exists(srcdir))
        print_status('Patch merges with source',
                     self.mergetree(os.path.join(tmpdir, 'head'), srcdir))

    def check_build(self, tmpdir, upwrap):
        # TODO lead_directory_missing
        srcdir = os.path.join(tmpdir, 'src', upwrap.directory)
        bindir = os.path.join(tmpdir, 'bin')
        setup_result = subprocess.call(['meson', 'setup', srcdir, bindir])
        print_status('meson setup', setup_result == 0)
        test_result = subprocess.call(['ninja', '-C', bindir, 'test'])
        print_status('ninja test', test_result == 0)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('--pull_request', type=int)
    parser.add_argument('--branch')
    parser.add_argument('--clone_url')
    parser.add_argument('--allow_other_files', action='store_true')
    parser.add_argument('--export_sources')
    args = parser.parse_args(args)
    if args.pull_request:
        r = Reviewer.from_pull_request(args.name, args.pull_request)
    elif args.branch:
        if args.clone_url:
            r = Reviewer.from_repository(args.name, args.clone_url,
                                         args.branch)
        else:
            r = Reviewer.from_committed(args.name, args.branch)
    else:
        sys.exit('Either --pull_request or --branch must be set')
    r.strict_fileset = not args.allow_other_files
    if not r.review(args.export_sources):
        sys.exit(1)

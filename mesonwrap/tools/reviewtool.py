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
import contextlib
import dataclasses
import enum
import hashlib
import os
import re
import shutil
import subprocess
import sys
from typing import List, Optional, Tuple

import git

from mesonwrap import ini
from mesonwrap import requests
from mesonwrap import tempfile
from mesonwrap.tools import environment
from mesonwrap.tools import publisher

OK_CHR = '\u2611'
FAIL_CHR = '\u2612'


class CheckError(Exception):
    pass


def print_status(msg, check: bool, fatal: bool = True, quiet: bool = False):
    """Prints msg with success indicator based on check parameter.
    Args:
        msg: str, status message to print
        check: success of the check
        fatal: if exception should be raised
        quiet: if message should be printed on success
    Raises: CheckError(msg) if not check and fatal
    """
    status = OK_CHR if check else FAIL_CHR
    if not quiet or not check:
        print(f'{msg}: {status}')
    if not check and fatal:
        raise CheckError(msg)


@enum.unique
class BuildStage(enum.IntEnum):

    NONE = enum.auto()
    CONFIGURE = enum.auto()
    BUILD = enum.auto()
    TEST = enum.auto()

    @classmethod
    def argparse(cls, value):
        return cls[value.upper()]

    def __str__(self):
        return self.name.lower()


@dataclasses.dataclass
class ReviewerOptions:
    meson_bin: str = 'meson'
    meson_args: List[str] = dataclasses.field(default_factory=list)
    strict_fileset: bool = True
    strict_version_in_url: bool = True
    strict_license_check: bool = True
    build_stage: BuildStage = BuildStage.TEST
    overwrite_merge: str = False
    export_sources: Optional[str] = None


class Reviewer:

    @classmethod
    def from_pull_request(cls, organization: str, project: str, pull_id: int):
        pull = environment.repo(organization, project).get_pull(pull_id)
        return cls(project=project, clone_url=pull.head.repo.clone_url,
                   branch=pull.base.ref, source_branch=pull.head.ref)

    @classmethod
    def from_committed(cls, organization: str, project: str, branch: str):
        return cls(project=project,
                   clone_url=environment.repo(organization, project).clone_url,
                   branch=branch)

    @classmethod
    def from_repository(cls, project, clone_url, branch):
        return cls(project=project, clone_url=clone_url, branch=branch)

    def __init__(self, project, clone_url, branch, source_branch=None):
        self._project = project
        self._clone_url = clone_url
        self._branch = branch
        self._source_branch = source_branch or branch
        self.options = ReviewerOptions()

    def review(self) -> Tuple[bool, Optional[str]]:
        with tempfile.TemporaryDirectory() as tmpdir:
            r = self.review_int(tmpdir)
            if self.options.export_sources:
                shutil.copytree(os.path.join(tmpdir, 'src'),
                                self.options.export_sources)
            return r

    def review_int(self, tmpdir) -> Tuple[bool, Optional[str]]:
        head_dir = os.path.join(tmpdir, 'head')
        with contextlib.closing(
                git.Repo.clone_from(self._clone_url, head_dir,
                                    branch=self._source_branch)) as head_repo:
            try:
                self.check_basics(head_repo)
                self.check_files(head_dir)
                upwrap = ini.WrapFile.from_file(
                    os.path.join(head_dir, 'upstream.wrap'))
                self.check_wrapformat(upwrap)
                self.check_url(upwrap)
                self.check_download(tmpdir, upwrap)
                self.check_extract(tmpdir, upwrap)
                self.check_build(tmpdir, upwrap)
                return (True, head_repo.head.object.hexsha)
            except CheckError:
                return (False, None)

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

    def check_url(self, upwrap):
        print_status('upstream.wrap has source_url with version substring',
                     self._branch in upwrap.source_url,
                     fatal=self.options.strict_version_in_url)

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
                     fatal=self.options.strict_fileset)

    @staticmethod
    def isfile(head_dir, filename):
        return os.path.isfile(os.path.join(head_dir, filename))

    def check_basics(self, head_repo):
        print(f'Inspecting project {self._project}, branch {self._branch}.')
        head_dir = head_repo.working_dir
        print_status('Repo name valid',
                     re.fullmatch('[a-z][a-z0-9._-]*', self._project))
        print_status('Branch name valid',
                     re.fullmatch('[a-z0-9._]+', self._branch))
        print_status('Target branch is not master', self._branch != 'master')
        print_status('Has readme.txt', self.isfile(head_dir, 'readme.txt'))
        print_status('Has LICENSE.build',
                     self.isfile(head_dir, 'LICENSE.build'),
                     fatal=self.options.strict_license_check)
        print_status('Has upstream.wrap',
                     self.isfile(head_dir, 'upstream.wrap'))

    @staticmethod
    def _fetch(url):
        data = None
        exc = None
        try:
            with requests.get(url) as rv:
                rv.raise_for_status()
                data = rv.content
        except Exception as e:  # pylint: disable=broad-except
            exc = e
        return (data, exc)

    def check_download(self, tmpdir, upwrap):
        source_data, download_exc = self._fetch(upwrap.source_url)
        try:
            print_status('Download URL works', download_exc is None)
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

    def mergetree(self, src, dst):
        for dirpath, dirnames, filenames in os.walk(src):
            prefix = os.path.relpath(dirpath, src)
            dstpath = os.path.join(dst, prefix)
            try:
                del dirnames[dirnames.index('.git')]
            except ValueError:
                pass  # it's fine if there is no .git directory
            for d in dirnames:
                os.makedirs(os.path.join(dstpath, d), exist_ok=True)
            for f in filenames:
                if f in ('readme.txt', 'upstream.wrap'):
                    continue
                dest = os.path.join(dstpath, f)
                print_status(f'{os.path.join(prefix, f)!r} already exists',
                             not os.path.exists(dest),
                             quiet=True,
                             fatal=not self.options.overwrite_merge)
                shutil.copy2(os.path.join(dirpath, f), dest)
        return True

    def check_extract(self, tmpdir, upwrap):
        srcdir_base = os.path.join(tmpdir, 'src')
        srcarchive = os.path.join(tmpdir, upwrap.source_filename)
        os.mkdir(srcdir_base)
        if upwrap.has_lead_directory_missing:
            os.mkdir(os.path.join(srcdir_base, upwrap.directory))
            shutil.unpack_archive(srcarchive,
                                  os.path.join(srcdir_base, upwrap.directory))
        else:
            shutil.unpack_archive(srcarchive, srcdir_base)
        srcdir = os.path.join(srcdir_base, upwrap.directory)
        try:
            print_status(f'upstream.wrap directory {upwrap.directory!r} exists',
                         os.path.exists(srcdir))
        except CheckError:
            files = os.listdir(srcdir_base)
            if len(files) >= 2:
                print('  available files:', files)
                print('  consider using "lead_directory_missing = true"')
            elif len(files) == 1:
                f, = files
                if os.path.isdir(files[0]):
                    print(f'  available directory: {f}')
                    print(f'  consider using "directory = {f}"')
                else:
                    print(f'  available file: {f}')
            else:
                print('  the archive is empty')
            raise
        print_status('Patch merges with source',
                     self.mergetree(os.path.join(tmpdir, 'head'), srcdir))

    def check_build(self, tmpdir, upwrap):
        srcdir = os.path.join(tmpdir, 'src', upwrap.directory)
        bindir = os.path.join(tmpdir, 'bin')
        if self.options.build_stage >= BuildStage.CONFIGURE:
            setup_result = subprocess.call([
                self.options.meson_bin, 'setup', srcdir, bindir
            ] + self.options.meson_args)
            print_status('meson setup', setup_result == 0)
        if self.options.build_stage >= BuildStage.BUILD:
            test_result = subprocess.call(['ninja', '-C', bindir])
            print_status('ninja build', test_result == 0)
        if self.options.build_stage >= BuildStage.TEST:
            test_result = subprocess.call(['ninja', '-C', bindir, 'test'])
            print_status('ninja test', test_result == 0)

    @staticmethod
    def merge(
        organization: str, project: str, pull_id: int, sha: str
    ) -> str:
        pull_request = (
            environment.repo(organization, project).get_pull(pull_id)
        )
        method = 'squash' if pull_request.commits > 1 else 'rebase'
        branch = pull_request.base.ref
        pull_request.merge(merge_method=method, sha=sha)
        return branch


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('name')
    parser.add_argument('--pull-request', type=int)
    parser.add_argument('--branch')
    parser.add_argument('--clone-url')
    parser.add_argument('--allow-other-files', action='store_true')
    parser.add_argument('--allow-url-without-version', action='store_true')
    parser.add_argument('--allow-no-license', action='store_true')
    parser.add_argument('--allow-overwrite', action='store_true')
    parser.add_argument('--build-stage', type=BuildStage.argparse,
                        choices=list(BuildStage), default=BuildStage.TEST)
    parser.add_argument('--meson', default='meson')
    parser.add_argument('--cross-file', action='append', default=[])
    parser.add_argument('--export-sources')
    parser.add_argument('--approve', action='store_true',
                        help='Approve and admit revision into WrapDB')
    parser.add_argument('--test',
                        action='store_const', const='mesonbuild-test',
                        dest='organization', default='mesonbuild',
                        help='Use mesonbuild-test organization')
    args = parser.parse_args(args)
    if args.pull_request:
        r = Reviewer.from_pull_request(args.organization,
                                       args.name, args.pull_request)
    elif args.branch:
        if args.clone_url:
            r = Reviewer.from_repository(args.name, args.clone_url,
                                         args.branch)
        else:
            r = Reviewer.from_committed(args.organization,
                                        args.name, args.branch)
    else:
        sys.exit('Either --pull-request or --branch must be set')
    r.options = ReviewerOptions(
        meson_bin=args.meson,
        strict_fileset=not args.allow_other_files,
        strict_version_in_url=not args.allow_url_without_version,
        strict_license_check=not args.allow_no_license,
        build_stage=args.build_stage,
        overwrite_merge=args.allow_overwrite,
        export_sources=args.export_sources)
    r.options.meson_args.extend(
        '--cross-file=' + os.path.abspath(cf) for cf in args.cross_file
    )
    review, sha = r.review()
    if not review:
        sys.exit(1)
    if args.approve:
        if args.pull_request is None:
            sys.exit('Must specify --approve and --pull-request together')
        version = Reviewer.merge(args.organization, args.name,
                                 args.pull_request, sha)
        publisher.publish(args.organization, args.name, version)

#!/usr/bin/env python

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
from pathlib import PurePath
import shutil
import tempfile
import zipfile

from mesonwrap import gitutils
from mesonwrap import upstream


_OUT_URL_BASE_DEFAULT = (
    'https://wrapdb.mesonbuild.com/v1/projects/%s/%s/%d/get_zip')

# relative fully qualified paths
_IGNORED_FILES = [
    '.gitignore',
    'readme.txt',
    'upstream.wrap',
]

_IGNORED_DIRS = [
    '.git',
]


class WrapCreator:

    def __init__(self, name, repo_url, branch, out_dir='.',
                 out_url_base=_OUT_URL_BASE_DEFAULT):
        self.name = name
        self.repo_url = repo_url
        self.branch = branch
        self.out_dir = out_dir
        self.out_url_base = out_url_base

    def create(self):
        with tempfile.TemporaryDirectory() as workdir:
            return self.create_internal(workdir)

    @staticmethod
    def _get_revision(repo):
        return gitutils.get_revision(repo, repo.head.commit)

    @staticmethod
    def check_definition(definition):
        for i in ['directory', 'source_url', 'source_filename', 'source_hash']:
            if not getattr(definition, 'has_' + i):
                raise RuntimeError('Missing {!r} in upstream.wrap.'.format(i))

    def make_zip(self, zippath, workdir):
        with zipfile.ZipFile(zippath, 'w',
                             compression=zipfile.ZIP_DEFLATED) as zip:
            for root, dirs, files in os.walk(workdir):
                relroot = PurePath(root).relative_to(workdir)
                dirs[:] = [p for p in dirs
                           if str(relroot / p) not in _IGNORED_DIRS]
                for f in files:
                    abspath = PurePath(root) / f
                    relpath = abspath.relative_to(workdir)
                    if str(relpath) in _IGNORED_FILES:
                        continue
                    zip.write(abspath, self.definition.directory / relpath)

    def create_internal(self, workdir):
        repo = git.Repo.clone_from(self.repo_url, workdir, branch=self.branch)
        upstream_file = os.path.join(workdir, 'upstream.wrap')
        revision_id = self._get_revision(repo)
        self.upstream_file = os.path.join(workdir, 'upstream.wrap')
        self.definition = upstream.UpstreamWrap.from_file(self.upstream_file)
        self.check_definition(self.definition)
        base_name = (self.name + '-' +
                     self.branch + '-' +
                     str(revision_id) + '-wrap')
        zip_name = base_name + '.zip'
        wrap_name = base_name + '.wrap'
        zip_full = os.path.join(self.out_dir, zip_name)
        wrap_full = os.path.join(self.out_dir, wrap_name)
        self.make_zip(zip_full, workdir)
        source_hash = hashlib.sha256(open(zip_full, 'rb').read()).hexdigest()
        with open(wrap_full, 'w') as wrapfile:
            url = self.out_url_base % (self.name, self.branch, revision_id)
            with open(upstream_file) as basewrap:
                # preserve whatever formatting user has provided
                wrapfile.write(basewrap.read())
            wrapfile.write('\n')
            wrapfile.write('patch_url = %s\n' % url)
            wrapfile.write('patch_filename = %s\n' % zip_name)
            wrapfile.write('patch_hash = %s\n' % source_hash)
        wrap_contents = open(wrap_full, 'r').read()
        zip_contents = open(zip_full, 'rb').read()
        return (wrap_contents, zip_contents, revision_id)


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('project_name')
    parser.add_argument('data_repo_url')
    parser.add_argument('branch')
    args = parser.parse_args(args)
    x = WrapCreator(args.project_name, args.data_repo_url, args.branch)
    x.create()

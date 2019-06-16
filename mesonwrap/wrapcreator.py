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
import contextlib
import hashlib
import io
import os
import zipfile
from pathlib import PurePath

import git

from mesonwrap import gitutils
from mesonwrap import tempfile
from mesonwrap import upstream
from mesonwrap import wrap

# Replace this with proper parameterized callback if this need to be extended.
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


def make_wrap(name: str, repo_url: str, branch: str) -> wrap.Wrap:
    with tempfile.TemporaryDirectory() as workdir:
        with contextlib.closing(
                git.Repo.clone_from(repo_url, workdir, branch=branch)) as repo:
            return _make_wrap(workdir, name, repo, branch)


def _check_definition(definition):
    for i in ['directory', 'source_url', 'source_filename', 'source_hash']:
        if not getattr(definition, 'has_' + i):
            raise RuntimeError('Missing {!r} in upstream.wrap.'.format(i))


def _make_zip(file, workdir, dirprefix):
    with zipfile.ZipFile(file, 'w',
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
                # Python 3.5 zipfile does not support pathlib
                zip.write(str(abspath), str(dirprefix / relpath))


def _make_wrap(workdir, name: str, repo: git.Repo, branch: str) -> wrap.Wrap:
    revision_id = gitutils.get_revision(repo, repo.head.commit)
    upstream_file = os.path.join(workdir, 'upstream.wrap')
    definition = upstream.UpstreamWrap.from_file(upstream_file)
    _check_definition(definition)
    with io.BytesIO() as zipf:
        _make_zip(zipf, workdir, definition.directory)
        zip_contents = zipf.getvalue()
    source_hash = hashlib.sha256(zip_contents).hexdigest()
    with io.StringIO() as wrapfile:
        url = _OUT_URL_BASE_DEFAULT % (name, branch, revision_id)
        with open(upstream_file) as basewrap:
            # preserve whatever formatting user has provided
            wrapfile.write(basewrap.read())
        wrapfile.write('\n')
        wrapfile.write('patch_url = %s\n' % url)
        zip_name = wrap.zip_name(name, branch, revision_id)
        wrapfile.write('patch_filename = %s\n' % zip_name)
        wrapfile.write('patch_hash = %s\n' % source_hash)
        wrap_contents = wrapfile.getvalue()
    return wrap.Wrap(name=name, version=branch, revision=revision_id,
                     wrap=wrap_contents, zip=zip_contents)


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('project_name')
    parser.add_argument('data_repo_url')
    parser.add_argument('branch')
    args = parser.parse_args(args)
    wrap = make_wrap(args.project_name, args.data_repo_url, args.branch)
    with open(wrap.wrap_name, 'w') as w:
        w.write(wrap.wrap)
    with open(wrap.zip_name, 'wb') as z:
        z.write(wrap.zip)

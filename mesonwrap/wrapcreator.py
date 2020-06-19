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
    'https://wrapdb.mesonbuild.com/v1/projects/{}/{}/{}/get_zip')

# relative fully qualified paths
_IGNORED_FILES = [
    '.gitignore',
    'readme.txt',
    'upstream.wrap',
    'wrapdb.ini',
]

_IGNORED_DIRS = [
    '.git',
]


def make_wrap(name: str, repo_url: str, branch: str) -> wrap.Wrap:
    with tempfile.TemporaryDirectory() as workdir:
        with contextlib.closing(
                git.Repo.clone_from(repo_url, workdir, branch=branch)) as repo:
            return _make_wrap(workdir, name, repo, branch)


def _check_wrapfile(wrapfile):
    for i in ['directory', 'source_url', 'source_filename', 'source_hash']:
        if not wrapfile.has(i):
            raise RuntimeError(f'Missing {i!r} in upstream.wrap.')


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
                zip.write(abspath, dirprefix / relpath)


def _make_wrap(workdir, name: str, repo: git.Repo, branch: str) -> wrap.Wrap:
    revision_commit_sha = repo.head.commit.hexsha
    revision_id = gitutils.get_revision(repo, repo.head.commit)
    upstream_file = os.path.join(workdir, 'upstream.wrap')
    wrapfile = upstream.WrapFile.from_file(upstream_file)
    _check_wrapfile(wrapfile)
    with io.BytesIO() as zipf:
        _make_zip(zipf, workdir, wrapfile.directory)
        zip_contents = zipf.getvalue()
    source_hash = hashlib.sha256(zip_contents).hexdigest()
    with io.StringIO() as wf:
        url = _OUT_URL_BASE_DEFAULT.format(name, branch, revision_id)
        with open(upstream_file) as basewrap:
            # preserve whatever formatting user has provided
            wf.write(basewrap.read())
        wf.write('\n')
        wf.write(f'patch_url = {url}\n')
        zip_name = wrap.zip_name(name, branch, revision_id)
        wf.write(f'patch_filename = {zip_name}\n')
        wf.write(f'patch_hash = {source_hash}\n')
        wrapfile_content = wf.getvalue()
    return wrap.Wrap(name=name, version=branch, revision=revision_id,
                     wrapfile_content=wrapfile_content, zip=zip_contents,
                     commit_sha=revision_commit_sha)


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('project_name')
    parser.add_argument('data_repo_url')
    parser.add_argument('branch')
    args = parser.parse_args(args)
    wrap = make_wrap(args.project_name, args.data_repo_url, args.branch)
    with open(wrap.wrapfile_name, 'w') as w:
        w.write(wrap.wrapfile_content)
    with open(wrap.zip_name, 'wb') as z:
        z.write(wrap.zip)

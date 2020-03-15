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

"""This script is used to initialise a Github repo to be
used as a basis for a Wrap db entry. Also calculates a basic
upstream.wrap."""

import argparse
import datetime
import hashlib

import git
import requests

from mesonwrap import gitutils, upstream
from mesonwrap.tools import environment


README = '''This repository contains a Meson build definition for project {reponame}.

For more information please see http://mesonbuild.com.
'''


MIT_LICENSE = '''Copyright (c) {year} The Meson development team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''


MAINTAINERS_TEAM_ID = {
    'mesonbuild': 2766876,
    'mesonbuild-test': 2767592,
}


class RepoBuilder:

    def __init__(self, name, path=None, organization=None, homepage=None):
        """Pushes to github only if organization is set."""
        self.name = name
        try:
            self.repo = git.Repo(path)
            try:
                self.origin = self.repo.remote('origin')
            except ValueError:
                self.origin = None
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            if organization is None:
                self.init(path)
            else:
                self.init_github(path, organization, homepage)

    def close(self):
        self.repo.close()

    def init(self, path, origin=None):
        """Push if origin is not None."""
        self.repo = git.Repo.init(path)
        self.refresh('Create repository for project %s' % self.name)
        if origin is not None:
            self.origin = self.repo.create_remote('origin', origin)
            self.origin.push(self.repo.head.ref.name)

    def refresh(self, message=None):
        if message is None:
            message = 'Refresh repository %s' % self.name
        with self.open('readme.txt', 'w') as ofile:
            ofile.write(README.format(reponame=self.name))
        with self.open('LICENSE.build', 'w') as ofile:
            ofile.write(MIT_LICENSE.format(year=datetime.datetime.now().year))
        self.repo.index.commit(message)

    def init_github(self, path, organization, homepage):
        gh = environment.github()
        mesonbuild = gh.get_organization(organization)
        description = 'Meson build definitions for %s' % self.name
        ghrepo = mesonbuild.create_repo(
            self.name, description=description, homepage=homepage,
            team_id=MAINTAINERS_TEAM_ID[organization])
        team = mesonbuild.get_team(MAINTAINERS_TEAM_ID[organization])
        team.set_repo_permission(ghrepo, 'push')
        self.init(path, ghrepo.ssh_url)

    def open(self, path, mode='r'):
        return gitutils.GitFile.open(self.repo, path, mode)

    @staticmethod
    def _get_hash(url):
        h = hashlib.sha256()
        with requests.get(url) as rv:
            rv.raise_for_status()
            h.update(rv.content)
        return h.hexdigest()

    def init_version(self, version):
        branch = self.repo.create_head(version)
        if self.origin is not None:
            self.origin.push(branch)

    def create_version(self, version, zipurl, filename, directory,
                       ziphash=None, base='HEAD'):
        if ziphash is None:
            ziphash = self._get_hash(zipurl)
        self.repo.head.reference = self.repo.create_head(version, commit=base)
        assert not self.repo.head.is_detached
        self.repo.head.reset(index=True, working_tree=True)
        with self.open('upstream.wrap', 'w') as ofile:
            upstream.UpstreamWrap(
                directory=directory,
                source_url=zipurl,
                source_filename=filename,
                source_hash=ziphash).write(ofile)


def new_repo(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('name')
    parser.add_argument('--directory', help='Working directory')
    parser.add_argument('--version', help='Initialize dummy version')
    parser.add_argument('--homepage', required=True)
    parser.add_argument('--test', action='store_true',
                        help='Publish to http://github.com/mesonbuild-test')
    args = parser.parse_args(args)
    organization = 'mesonbuild-test' if args.test else 'mesonbuild'
    builder = RepoBuilder(name=args.name,
                          path=args.directory,
                          organization=organization,
                          homepage=args.homepage)
    if args.version:
        builder.init_version(args.version)


def refresh(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('name')
    parser.add_argument('--directory', help='Working directory')
    parser.add_argument('--message')
    args = parser.parse_args(args)
    builder = RepoBuilder(name=args.name, path=args.directory)
    builder.refresh(args.message)


def new_version(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('name')
    parser.add_argument('--directory', help='Working directory')
    parser.add_argument('--version', required=True)
    parser.add_argument('--zipurl', required=True)
    parser.add_argument('--filename', required=True)
    parser.add_argument('--srcdir', required=True)
    args = parser.parse_args(args)
    builder = RepoBuilder(name=args.name, path=args.directory)
    builder.create_version(args.version, args.zipurl, args.filename,
                           args.srcdir)

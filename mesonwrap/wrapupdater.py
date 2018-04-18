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
import os
import tempfile, shutil

from mesonwrap import wrapdb, wrapcreator


class WrapUpdater:
    def __init__(self, dbdir='.'):
        self.dbdir = dbdir
        self.db = wrapdb.WrapDatabase(self.dbdir, True)

    def close(self):
        self.db.close()

    def update_db(self, project_name, repo_url, branch):
        with tempfile.TemporaryDirectory() as workdir:
            creator = wrapcreator.WrapCreator(project_name, repo_url, branch, workdir)
            (wrap_contents, zip_contents, revision_id) = creator.create()
            self.db.insert(project_name, branch, revision_id, wrap_contents, zip_contents)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('repo_url')
    parser.add_argument('branch')
    args = parser.parse_args(args)
    m = WrapUpdater()
    m.update_db(args.project, args.repo_url, args.branch)

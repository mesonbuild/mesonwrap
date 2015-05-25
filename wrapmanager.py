#!/usr/bin/env python3

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

import wrapdb, wrapcreator
import sys, os
import tempfile

class WrapManager: # Don't you just love Java-inspired names?
    
    def __init__(self, dbdir='.'):
        self.dbdir = dbdir
        self.db = wrapdb.WrapDatabase(self.dbdir)

    def update_db(self, project_name, repo_url, branch):
        with tempfile.TemporaryDirectory() as workdir:
            creator = wrapcreator.WrapCreator(project_name, repo_url, branch, workdir)
            (wrap_fname, zip_fname, revision_id) = creator.create()
            wrap_contents = open(wrap_fname, 'r').read()
            zip_contents = open(zip_fname, 'rb').read()
            self.db.insert(project_name, branch, revision_id, wrap_contents, zip_contents)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(sys.argv[0], 'project repo_url branch')
        sys.exit(1)
    m = WrapManager()
    m.update_db(sys.argv[1], sys.argv[2], sys.argv[3])

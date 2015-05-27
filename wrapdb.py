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

import sqlite3
import os, sys

class WrapDatabase:
    def __init__(self, dirname):
        self.fname = os.path.join(dirname, 'wrapdb.sqlite')
        if not os.path.exists(self.fname):
            self.create_db()
        else:
            self.conn = sqlite3.connect(self.fname)

    def close(self):
        self.conn.close()

    def insert(self, project, branch, revision, wrap, zip):
        assert(isinstance(wrap, str))
        assert(isinstance(zip, bytes))
        assert(isinstance(revision, int))
        c = self.conn.cursor()
        project = project.lower()
        branch = branch.lower()
        c.execute('''INSERT OR REPLACE INTO wraps VALUES (?, ?, ?, ?, ?);''', (project, branch, revision, wrap,
                                                                               sqlite3.Binary(zip)))
        self.conn.commit()

    def name_search(self, text):
        c = self.conn.cursor()
        c.execute('''SELECT DISTINCT project FROM wraps WHERE project LIKE ?;''', (text+'%',))
        return c.fetchall()

    def get_versions(self, project):
        c = self.conn.cursor()
        c.execute('''SELECT branch, revision FROM wraps WHERE project == ?;''', (project,))
        return c.fetchall()

    def get_wrap(self, project, branch, revision):
        c = self.conn.cursor()
        try:
            c.execute('''SELECT wrap FROM wraps WHERE project == ? AND branch == ? AND revision == ?;''',
                      (project, branch, revision))
            return c.fetchone()[0]
        except Exception as e:
            return None

    def get_zip(self, project, branch, revision):
        c = self.conn.cursor()
        try:
            c.execute('''SELECT zip FROM wraps WHERE project == ? AND branch == ? AND revision == ?;''',
                      (project, branch, revision))
            return c.fetchone()[0]
        except Exception as e:
            return None

    def create_db(self):
        self.conn = sqlite3.connect(self.fname)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE wraps
        (project TEXT NOT NULL, branch TEXT NOT NULL, revision INTEGER, wrap TEXT NOT NULL, zip BLOB NOT NULL
        CHECK (revision > 0));''')
        c.execute('''CREATE UNIQUE INDEX wrapindex ON wraps(project, branch, revision);''')
        c.execute('''CREATE INDEX namesearch ON wraps(project);''')
        self.conn.commit()

if __name__ == '__main__':
    db = WrapDatabase('.')
    db.insert('zlib', '1.2.8', 1, 'foobar', b'barfoo')

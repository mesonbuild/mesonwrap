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

from distutils import version
import sqlite3
import os


class WrapDatabase:
    def __init__(self, dirname, readwrite=False):
        self.fname = os.path.join(dirname, 'wrapdb.sqlite')
        if not os.path.exists(self.fname):
            self.create_db()
        if readwrite:
            self.conn = sqlite3.connect(self.fname)
        else:
            dburi = 'file:' + self.fname + '?mode=ro'
            self.conn = sqlite3.connect(dburi, uri=True)

    def close(self):
        self.conn.close()

    def insert(self, project, branch, revision, wrap, zip):
        assert isinstance(wrap, str)
        assert isinstance(zip, bytes)
        assert isinstance(revision, int)
        c = self.conn.cursor()
        project = project.lower()
        branch = branch.lower()
        c.execute('''INSERT OR REPLACE INTO wraps VALUES (?, ?, ?, ?, ?);''',
                  (project, branch, revision, wrap, sqlite3.Binary(zip)))
        self.conn.commit()

    def name_search(self, text):
        c = self.conn.cursor()
        query = '''SELECT DISTINCT project FROM wraps
                   WHERE project LIKE ? ORDER BY project;'''
        c.execute(query, (text + '%',))
        return [x[0] for x in c.fetchall()]

    def get_versions(self, project, latest=False):
        c = self.conn.cursor()
        query = '''SELECT branch, revision FROM wraps
                   WHERE project == ?
                   ORDER BY branch DESC, revision DESC;'''
        c.execute(query, (project,))
        if latest:
            # TODO consider computing this during import
            latest_ver = max((version.LooseVersion(r[0]), r[1])
                             for r in c.fetchall())
            return [(str(latest_ver[0]), latest_ver[1])]
        else:
            return c.fetchall()

    def get_wrap(self, project, branch, revision):
        c = self.conn.cursor()
        try:
            c.execute('''SELECT wrap FROM wraps
                         WHERE project == ? AND
                               branch == ? AND
                               revision == ?;''',
                      (project, branch, revision))
            return c.fetchone()[0]
        except Exception as e:
            return None

    def get_zip(self, project, branch, revision):
        c = self.conn.cursor()
        try:
            c.execute('''SELECT zip FROM wraps
                         WHERE project == ? AND
                               branch == ? AND
                               revision == ?;''',
                      (project, branch, revision))
            return c.fetchone()[0]
        except Exception as e:
            return None

    def create_db(self):
        self.conn = sqlite3.connect(self.fname)
        c = self.conn.cursor()
        c.execute('''
        CREATE TABLE wraps
        (project TEXT NOT NULL,
         branch TEXT NOT NULL,
         revision INTEGER,
         wrap TEXT NOT NULL,
         zip BLOB NOT NULL
         CHECK (revision > 0));''')
        c.execute('''CREATE UNIQUE INDEX wrapindex ON
                     wraps(project, branch, revision);''')
        c.execute('''CREATE INDEX namesearch ON wraps(project);''')
        self.conn.commit()
        self.close()

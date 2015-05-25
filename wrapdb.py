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

import sqlite3
import os, sys

class WrapDatabase:
    def __init__(self, dirname):
        self.fname = os.path.join(dirname, 'wrapdb.sqlite')
        try:
            os.unlink(self.fname)
        except FileNotFoundError:
            pass
        if not os.path.exists(self.fname):
            self.create_db()
        else:
            self.conn = sqlite3.connect(self.fname)

    def create_db(self):
        self.conn = sqlite3.connect(self.fname)
        c = self.conn.cursor()
        c.execute('''CREATE TABLE wraps
        (project TEXT NOT NULL, branch TEXT NOT NULL, revision INTEGER, content TEXT NOT NULL
        CHECK (revision > 0));''')
        c.execute('''CREATE UNIQUE INDEX wrapindex ON wraps(project, branch, revision);''')
        c.execute('''CREATE INDEX namesearch ON wraps(project);''')
        self.conn.commit()

if __name__ == '__main__':
    db = WrapDatabase('.')
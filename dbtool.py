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

import wrapdb
import sys, os

# This is a simple tool to do queries and inserts from the command line.

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(sys.argv[0], 'dbdir queryterm or --arg queryterm')
        sys.exit(1)

    dbdir = sys.argv[1]
    first = sys.argv[2]
    rest = sys.argv[3:]
    db = wrapdb.WrapDatabase(dbdir)
    if first == '--wrap':
        print(db.get_wrap(*rest))
    elif first == '--versions':
        print(db.get_versions(*rest))
    elif first == '--zip':
        print(db.get_zip(*rest))
    elif first == '--insert':
        rest[2] = int(rest[2])
        rest[4] = rest[4].encode()
        db.insert(*rest)
    else:
        for i in db.name_search(first):
            print(i[0])

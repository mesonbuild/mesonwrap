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
import sys, os

from mesonwrap import wrapdb


# This is a simple tool to do queries and inserts from the command line.

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--dbdir', required=True)
    parser.add_argument('command', choices=('wrap', 'versions', 'zip', 'insert', 'search'))
    args, rest = parser.parse_known_args(args)
    db = wrapdb.WrapDatabase(args.dbdir)
    if args.command == 'wrap':
        print(db.get_wrap(*rest))
    elif args.command == 'versions':
        print(db.get_versions(*rest))
    elif args.command == 'zip':
        print(db.get_zip(*rest))
    elif args.command == 'insert':
        rest[2] = int(rest[2])
        rest[4] = rest[4].encode()
        db.insert(*rest)
    elif args.command == 'search':
        for i in db.name_search(rest[0]):
            print(i[0])
    else:
        sys.exit('Unrecognized command {!r}'.format(args.command))

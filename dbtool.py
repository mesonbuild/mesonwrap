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

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(sys.argv[0], 'queryterm')
        sys.exit(1)
    qterm = sys.argv[1]
    db = wrapdb.WrapDatabase('.')
    for i in db.name_search(qterm):
        print(i)
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

"""This script reads config.h.meson, looks for header
checks and writes the corresponding meson declaration.

Copy config.h.in to config.h.meson, replace #undef
with #mesondefine and run this.
"""

import sys

for line in open(sys.argv[1]):
    line = line.strip()
    if line.startswith('#mesondefine') and \
       line.endswith('_H'):
        token = line.split()[1]
        tarr = token.split('_')[1:-1]
        tarr = [x.lower() for x in tarr]
        hname = '/'.join(tarr) + '.h'
        print("  ['%s', '%s']," % (hname, token))

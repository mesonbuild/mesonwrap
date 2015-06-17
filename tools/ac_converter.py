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

print('check_headers = [')

for line in open(sys.argv[1]):
    line = line.strip()
    if line.startswith('#mesondefine') and \
       line.endswith('_H'):
        token = line.split()[1]
        tarr = token.split('_')[1:-1]
        tarr = [x.lower() for x in tarr]
        hname = '/'.join(tarr) + '.h'
        print("  ['%s', '%s']," % (token, hname))
print(']\n')

print('''foreach h : check_headers
  if cc.has_header(h.get(1))
    cdata.set(h.get(0), 1)
  endif
endforeach
''')

# Add stuff here as it is encountered.
function_data = \
    {'HAVE_FEENABLEEXCEPT' : ('feenableexcept', 'fenv.h'),
     'HAVE_MMAP' : ('mmap', 'sys/mman.h'),
     'HAVE_GETPAGESIZE' : ('getpagesize', 'unistd.h'),
     'HAVE_GETISAX' : ('getisax', 'sys/auxv.h'),
     'HAVE_GETTIMEOFDAY' : ('gettimeofday', 'sys/time.h'),
     'HAVE_MPROTECT' : ('mprotect', 'sys/mman.h'),
     'HAVE_POSIX_MEMALIGN' : ('posix_memalign', 'stdlib.h'),
     'HAVE_SIGACTION' : ('sigaction', 'signal.h'),
     
     }

print('check_functions = [')

for line in open(sys.argv[1]):
    try:
        token = line.split()[1]
        fdata = function_data[token]
        print("  ['%s', '%s', '#include<%s>']," % (token, fdata[0], fdata[1]))
    except Exception:
        pass
print(']\n')

print('''foreach f : check_functions
  if cc.has_function(f.get(1), prefix : f.get(2))
    cdata.set(f.get(0), 1)
  endif
endforeach
''')

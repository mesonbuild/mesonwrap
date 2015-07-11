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
     'HAVE_FECLEAREXCEPT' : ('feclearexcept', 'fenv.h'),
     'HAVE_FEDISABLEEXCEPT' : ('fedisableexcept', 'fenv.h'),
     'HAVE_MMAP' : ('mmap', 'sys/mman.h'),
     'HAVE_GETPAGESIZE' : ('getpagesize', 'unistd.h'),
     'HAVE_GETISAX' : ('getisax', 'sys/auxv.h'),
     'HAVE_GETTIMEOFDAY' : ('gettimeofday', 'sys/time.h'),
     'HAVE_MPROTECT' : ('mprotect', 'sys/mman.h'),
     'HAVE_POSIX_MEMALIGN' : ('posix_memalign', 'stdlib.h'),
     'HAVE_SIGACTION' : ('sigaction', 'signal.h'),
     'HAVE_ALARM' : ('alarm', 'unistd.h'),
     'HAVE_CLOCK_GETTIME' : ('clock_gettime', 'time.h'),
     'HAVE_CTIME_R' : ('ctime_r', 'time.h'),
     'HAVE_DRAND48' : ('drand48', 'stdlib.h'),
     'HAVE_FLOCKFILE' : ('flockfile', 'stdio.h'),
     'HAVE_FORK' : ('fork', 'unistd.h'),
     'HAVE_FUNLOCKFILE' : ('funlockfile', 'stdio.h'),
     'HAVE_GETLINE' : ('getline', 'stdio.h'),
     'HAVE_LINK' : ('link', 'unistd.h'),
     'HAVE_RAISE' : ('raise', 'signal.h'),
     'HAVE_STRNDUP' : ('strndup', 'string.h'),
     'HAVE_SCHED_GETAFFINITY' : ('sched_getaffinity', 'sched.h'),
     'HAVE_WAITPID' : ('waitpid', 'sys/wait.h'),
     'HAVE_XRENDERCREATECONICALGRADIENT' : ('XRenderCreateConicalGradient', 'xcb/render.h'),
     'HAVE_XRENDERCREATELINEARGRADIENT' : ('XRenderCreateLinearGradient', 'xcb/render.h'),
     'HAVE_XRENDERCREATERADIALGRADIENT' : ('XRenderCreateRadialGradient', 'xcb/render.h'),
     'HAVE_XRENDERCREATESOLIDFILL' : ('XRenderCreateSolidFill', 'xcb/render.h'),
     'HAVE_DCGETTEXT': ('dcgettext', 'libintl.h'),
     'HAVE_ENDMNTENT': ('endmntent', 'mntent.h'),
     'HAVE_ENDSERVENT' : ('endservent', 'netdb.h'),
     'HAVE_EVENTFD': ('eventfd', 'sys/eventfd.h'),
     'HAVE_FALLOCATE': ('fallocate', 'fcntl.h'),
     'HAVE_FCHMOD': ('fchmod', 'sys/stat.h'),
     'HAVE_FCHOWN': ('fchown', 'unistd.h'),
     'HAVE_FDWALK': ('fdwalk', 'stdlib.h'),
     'HAVE_FSYNC': ('fsync', 'unistd.h'),
     'HAVE_GETC_UNLOCKED': ('getc_unlocked', 'stdio.h'),
     'HAVE_GETFSSTAT': ('getfsstat', 'sys/mount.h'),
     'HAVE_GETMNTENT_R': ('getmntent_r', 'mntent.h'),
     'HAVE_GETPROTOBYNAME_R': ('getprotobyname_r', 'netdb.h'),
     'HAVE_GETRESUID' : ('getresuid', 'unistd.h'),
     'HAVE_GETVFSSTAT' : ('getvfsstat', 'sys/statvfs.h'),
     'HAVE_GMTIME_R' : ('gmtime_r', 'time.h'),
     'HAVE_HASMNTOPT': ('hasmntopt', 'mntent.h'),
     'HAVE_IF_INDEXTONAME': ('if_indextoname', 'net/if.h'),
     'HAVE_IF_NAMETOINDEX': ('if_nametoindex', 'net/if.h'),
     'HAVE_INOTIFY_INIT1': ('inotify_init1', 'sys/inotify.h'),
     'HAVE_ISSETUGID': ('issetugid', 'unistd.h'),
     'HAVE_KEVENT': ('kevent', 'sys/event.h'),
     'HAVE_KQUEUE': ('kqueue', 'sys/event.h'),
     'HAVE_LCHMOD': ('lchmod', 'sys/stat.h'),
     'HAVE_LCHOWN': ('lchown', 'unistd.h'),
     'HAVE_LSTAT': ('lstat', 'sys/stat.h'),
     'HAVE_MEMCPY': ('memcpy', 'string.h'),
     'HAVE_MEMALIGN': ('memalign', 'stdlib.h'),
     'HAVE_MEMMEM': ('memmem', 'string.h'),
     'HAVE_NEWLOCALE': ('newlocale', 'locale.h'),
     'HAVE_PIPE2': ('pipe2', 'fcntl.h'),
     'HAVE_POLL': ('poll', 'poll.h'),
     'HAVE_PRLIMIT': ('prlimit', 'sys/resource.h'),
     'HAVE_PTHREAD_ATTR_SETSTACKSIZE': ('pthread_attr_setstacksize', 'pthread.h'),
     'HAVE_PTHREAD_CONDATTR_SETCLOCK': ('pthread_condattr_setclock', 'pthread.h'),
     'HAVE_PTHREAD_COND_TIMEDWAIT_RELATIVE_NP': ('pthread_cond_timedwait_relative_np', 'pthread.h'),
     'HAVE_READLINK': ('readlink', 'unistd.h'),
     'HAVE_RES_INIT': ('res_init', 'resolv.h'),
     'HAVE_SENDMMSG': ('sendmmsg', 'sys/socket.h'),
     'HAVE_SETENV': ('setenv', 'stdlib.h'),
     'HAVE_SETMNTENT': ('setmntent', 'mntent.h'),
     'HAVE_SNPRINTF': ('snprintf', 'stdio.h'),
     'HAVE_SPLICE': ('splice', 'fcntl.h'),
     'HAVE_STATFS': ('statfs', 'mount.h'),
     'HAVE_STATVFS': ('statvfs', 'sys/statvfs.h'),
     'HAVE_STPCOPY': ('stpcopy', 'string.h'),
     'HAVE_STRCASECMP': ('strcasecmp', 'strings.h'),
     'HAVE_STRLCPY': ('strlcpy', 'string.h'),
     'HAVE_STRNCASECMP': ('strncasecmp', 'strings.h'),
     'HAVE_STRSIGNAL': ('strsignal', 'signal.h'),
     'HAVE_STRTOD_L': ('strtod_l', 'stdlib.h'),
     'HAVE_STRTOLL_L': ('strtoll_l', 'stdlib.h'),
     'HAVE_STRTOULL_L': ('strtoull_l', 'stdlib.h'),
     'HAVE_SYMLINK': ('symlink', 'unistd.h'),
     'HAVE_SYSCTLBYNAME': ('sysctlbyname', 'sys/sysctl.h'),
     'HAVE_TIMEGM': ('timegm', 'time.h'),
     'HAVE_UNSETENV': ('unsetenv', 'stdlib.h'),
     'HAVE_USELOCALE': ('uselocale', 'xlocale.h'),
     'HAVE_UTIMES': ('utimes', 'sys/time.h'),
     'HAVE_VALLOC': ('valloc', 'stdlib.h'),
     'HAVE_VASPRINTF': ('vasprintf', 'stdio.h'),
     'HAVE_VSNPRINTF': ('vsnprintf', 'stdio.h'),
     'HAVE_BCOPY': ('bcopy', 'strings.h'),
     'HAVE_STRERROR': ('strerror', 'string.h'),
     'HAVE_MEMMOVE': ('memmove', 'string.h'),
     'HAVE_STRTOIMAX': ('strtoimax', 'inttypes.h'),
     'HAVE_STRTOLL': ('strtoll', 'stdlib.h'),
     'HAVE_STRTOQ': ('strtoq', 'stdlib.h'),
    }

print('check_functions = [')

for line in open(sys.argv[1]):
    try:
        token = line.split()[1]
        if token in function_data:
            fdata = function_data[token]
            print("  ['%s', '%s', '#include<%s>']," % (token, fdata[0], fdata[1]))
        elif token.startswith('HAVE_') and not token.endswith('_H'):
            print('# check token', token)
    except Exception:
        pass
print(']\n')

print('''foreach f : check_functions
  if cc.has_function(f.get(1), prefix : f.get(2))
    cdata.set(f.get(0), 1)
  endif
endforeach
''')

# Convert sizeof checks.

for line in open(sys.argv[1]):
    arr = line.strip().split()
    if len(arr) != 2:
        continue
    elem = arr[1]
    if elem.startswith('SIZEOF_'):
        typename = elem.split('_', 1)[1].replace('_P', '*').replace('_', ' ').lower().replace('size t', 'size_t')
        print("cdata.set('%s', cc.sizeof('%s'))" % (elem, typename))

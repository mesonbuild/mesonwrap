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

"""This script is used to initialise a Github repo to be
used as a basis for a Wrap db entry. Also calculates a basic
upstream.wrap."""

import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request

upstream_templ = '''[wrap-file]
directory = %s

source_url = %s
source_filename = %s
source_hash = %s
'''

def initialize(reponame):
    subprocess.check_call(['git', 'init'])
    ofile = open('readme.txt', 'w')
    ofile.write('''This repository contains a Meson build definition for project %s.

All files in this repository have the same license as the original project.

For more information please see http://mesonbuild.com.
''' % reponame)
    ofile.close()
    subprocess.check_call(['git', 'add', 'readme.txt'])
    subprocess.check_call(['git', 'commit', '-a', '-m', 'Created repository for project %s.' % reponame])
    subprocess.check_call(['git', 'tag', 'commit_zero', '-a', '-m', 'A tag that helps get revision ids for releases.'])
    subprocess.check_call(['git', 'remote', 'add', 'origin', 'git@github.com:mesonbuild/%s.git' % reponame])
    subprocess.check_call(['git', 'push', '-u', 'origin', 'master'])
    subprocess.check_call(['git', 'push', '--tags'])
    shutil.rmtree('.git')
    os.unlink('readme.txt')

def build_upstream_wrap(zipurl, filename, directory):
    with urllib.request.urlopen(zipurl) as r:
        data = r.read()
        open(filename, 'wb').write(data)
        h = hashlib.sha256()
        h.update(data)
        dhash = h.hexdigest()
        ofile = open('upstream.wrap', 'w')
        ofile.write(upstream_templ % (directory, zipurl, filename, dhash))
        ofile.close()


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(sys.argv[0], '<reponame> <zipurl> <filename> <directory>')
        sys.exit(1)
    reponame = sys.argv[1]
    zipurl = sys.argv[2]
    filename = sys.argv[3]
    directory = sys.argv[4]
    initialize(reponame)
    build_upstream_wrap(zipurl, filename, directory)
    print('Done, now do the branching + stuff.')


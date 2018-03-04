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

import datetime
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

readme = '''This repository contains a Meson build definition for project {reponame}.

For more information please see http://mesonbuild.com.
'''


mit_license = '''Copyright (c) {year} The Meson development team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''


def initialize(reponame):
    subprocess.check_call(['git', 'init'])
    with open('readme.txt', 'w') as ofile:
        ofile.write(readme.format(reponame=reponame))
    with open('LICENSE.build', 'w') as ofile:
        ofile.write(mit_license.format(year=datetime.datetime.now().year))
    subprocess.check_call(['git', 'add', 'readme.txt', 'LICENSE.build'])
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
        with open('upstream.wrap', 'w') as ofile:
            ofile.write(upstream_templ % (directory, zipurl, filename, dhash))


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


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

import sys, os, re
import urllib.request, json, hashlib
import tempfile, subprocess
import configparser

class Reviewer:
    def __init__(self, project):
        pull_id = 2
        self.parse_url(project, pull_id)

    def parse_url(self, project, pull_id):
        data_url = 'https://api.github.com/repos/mesonbuild/%s/pulls/%d' % (project, pull_id)
        with urllib.request.urlopen(data_url) as u:
            text = u.read().decode()
            self.values = json.loads(text)

    def review(self):
        with tempfile.TemporaryDirectory() as base_dir:
            with tempfile.TemporaryDirectory() as head_dir:
                self.review_int(base_dir, head_dir)

    def clone_repos(self, base_dir, head_dir):
        branch = self.values['base']['ref']
        base_git = self.values['base']['repo']['clone_url']
        head_git = 'https://github.com/%s/%s.git' % (self.values['head']['user']['login'],
                                                     self.values['base']['repo']['name'])
        subprocess.check_call(['git', 'clone', '-b', branch, base_git, base_dir],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(['git', 'clone', '-b', branch, head_git, head_dir],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def review_int(self, base_dir, head_dir):
        #print(json.dumps(self.values, sort_keys=True, indent=4))
        project = self.values['base']['repo']['name']
        branch = self.values['base']['ref']
        self.clone_repos(base_dir, head_dir)
        rval = self.check_basics(base_dir, head_dir, project, branch)
        if rval != 0:
            return rval
        rval = self.check_download(os.path.join(head_dir, 'upstream.wrap'))
        rval = self.check_files(head_dir)
        return rval

    def check_files(self, head_dir):
        found = False
        permitted_files = ['upstream.wrap', 'meson.build', 'readme.txt',
                           'meson_options.txt', '.gitignore']
        for root, dirs, files in os.walk(head_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            for fname in files:
                if fname not in permitted_files:
                    if not found:
                        print('Non-buildsystem files found:')
                    found = True
                    abs_name = os.path.join(root, fname)
                    rel_name = abs_name[len(head_dir)+1:]
                    print(' ', rel_name)
        if not found:
            print('Repo contains only buildsystem files: YES')

    def check_basics(self, base_dir, head_dir, project, branch):
        print('Inspecting project %s, branch %s.' % (project, branch))

        if re.fullmatch('[a-z0-9._]+', project):
            print('Repo name valid: YES')
        else:
            print('Repo name valid: NO')
            return 1
        if re.fullmatch('[a-z0-9._]+', branch):
            print('Branch name valid: YES')
        else:
            print('Branch name valid: NO')
            return 1
        if branch != 'master':
            print('Target branch is not master: YES')
        else:
            print('Target branch is not master: NO')
            return 1
        output = subprocess.check_output(['git', 'tag'], cwd=base_dir).decode()
        if 'commit_zero' in output:
            print('Has commit_zero: YES')
        else:
            print('Has commit_zero: NO')
            return 1
        if os.path.isfile(os.path.join(head_dir, 'readme.txt')):
            print('Has readme.txt: YES')
        else:
            print('Has readme.txt: NO')
            return 1
        upwrap = os.path.join(head_dir, 'upstream.wrap')
        if os.path.isfile(upwrap):
            print('Has upstream.wrap: YES')
        else:
            print('Has upstream.wrap: NO')
            return 1
        if os.path.isfile(os.path.join(head_dir, 'meson.build')):
            print('Has toplevel meson.build: YES')
        else:
            print('Has toplevel meson.build: NO')
            return 1
        return 0

    def check_download(self, upwrap):
        config = configparser.ConfigParser()
        config.read(upwrap)
        dl_url = config['wrap-file']['source_url']
        expected_hash = config['wrap-file']['source_hash']
        try:
            with urllib.request.urlopen(dl_url) as u:
                bytes = u.read()
        except Exception as e:
            print('Download url works: NO\n  ' + str(e))
            return 1
        print('Download url works: YES')
        h = hashlib.sha256()
        h.update(bytes)
        calculated_hash = h.hexdigest()
        if calculated_hash == expected_hash:
            print('Hash matches: YES')
        else:
            print('Hash matches: NO')
            print(' expected:', expected_hash)
            print('      got:', calculated_hash)
            return 1
        return 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(sys.argv[0], '<project name>')
        sys.exit(1)
    r = Reviewer(sys.argv[1])
    sys.exit(r.review())

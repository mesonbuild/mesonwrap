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

import sys, os
import urllib.request, json
import tempfile, subprocess

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
        subprocess.check_call(['git', 'clone', '-b', branch, base_git, base_dir])
        subprocess.check_call(['git', 'clone', '-b', branch, head_git, head_dir])

    def review_int(self, base_dir, head_dir):
        #print(json.dumps(self.values, sort_keys=True, indent=4))
        project = self.values['base']['repo']['name']
        branch = self.values['base']['ref']
        self.clone_repos(base_dir, head_dir)
        print('Inspecting project %s, branch %s.' % (project, branch))
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
        if os.path.isfile(os.path.join(head_dir, 'upstream.wrap')):
            print('Has upstream.wrap: YES')
        else:
            print('Has upstream.wrap: NO')
            return 1
        return 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(sys.argv[0], '<project name>')
        sys.exit(1)
    r = Reviewer(sys.argv[1])
    sys.exit(r.review())
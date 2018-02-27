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


def print_status(msg, check):
    '''
    Prints msg with success indicator based on check parameter.
    Returns: check
    '''
    OK_CHR = '\u2611'
    FAIL_CHR = '\u2612'
    status = OK_CHR if check else FAIL_CHR
    print('{msg}: {status}'.format(msg=msg, status=status))
    return check


class Reviewer:
    def __init__(self, project, pull_id):
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
        if not self.check_basics(base_dir, head_dir, project, branch): return False
        if not self.check_files(head_dir): return False
        if not self.check_wrapformat(os.path.join(head_dir, 'upstream.wrap')): return False
        if not self.check_download(os.path.join(head_dir, 'upstream.wrap')): return False
        return True

    def check_wrapformat(self, upwrap):
        config = configparser.ConfigParser()
        config.read(upwrap)
        if not print_status('Has wrap-file section', 'wrap-file' in config): return False
        sec = config['wrap-file']
        if not print_status('Section has directory', 'directory' in sec): return False
        if not print_status('Section has source_url', 'source_url' in sec): return False
        if not print_status('Section has source_filename', 'source_filename' in sec): return False
        if not print_status('Section has source_hash', 'source_hash' in sec): return False
        return True

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
        if not print_status('Repo contains only buildsystem files', not found):
            return False
        return True

    @staticmethod
    def git_tags(git_root):
        return subprocess.check_output(['git', 'tag'], cwd=git_root).decode()

    @staticmethod
    def isfile(head_dir, filename):
        return os.path.isfile(os.path.join(head_dir, filename))

    def check_basics(self, base_dir, head_dir, project, branch):
        print('Inspecting project %s, branch %s.' % (project, branch))

        if not print_status('Repo name valid', re.fullmatch('[a-z0-9._]+', project)): return False
        if not print_status('Branch name valid', re.fullmatch('[a-z0-9._]+', branch)): return False
        if not print_status('Target branch is not master', branch != 'master'): return False
        if not print_status('Has commit_zero', 'commit_zero' in self.git_tags(base_dir)): return False
        if not print_status('Has readme.txt', self.isfile(head_dir, 'readme.txt')): return False
        if not print_status('Has upstream.wrap', self.isfile(head_dir, 'upstream.wrap')): return False
        if not print_status('Has toplevel meson.build', self.isfile(head_dir, 'meson.build')): return False
        return True

    @staticmethod
    def _fetch(url):
        data = None
        exc = None
        try:
            with urllib.request.urlopen(url) as u:
                data = u.read()
        except Exception as e:
            exc = e
        return (data, exc)

    def check_download(self, upwrap):
        config = configparser.ConfigParser()
        config.read(upwrap)
        dl_url = config['wrap-file']['source_url']
        expected_hash = config['wrap-file']['source_hash']
        source_data, download_exc = self._fetch(dl_url)
        if not print_status('Download url works', download_exc is None):
            print(' error:', str(e))
            return False
        h = hashlib.sha256()
        h.update(source_data)
        calculated_hash = h.hexdigest()
        if not print_status('Hash matches', calculated_hash == expected_hash):
            print(' expected:', expected_hash)
            print('      got:', calculated_hash)
            return False
        return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(sys.argv[0], '<project name> <merge request number>')
        sys.exit(1)
    pull_id = int(sys.argv[2])
    r = Reviewer(sys.argv[1], pull_id)
    sys.exit(r.review())


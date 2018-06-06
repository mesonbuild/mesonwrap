# Copyright 2015 The Meson development team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import flask
# GitHub secret key support
import hashlib
import hmac

from mesonwrap import wrapupdater
from wrapweb import jsonstatus
from wrapweb.app import APP


RESTRICTED_PROJECTS = [
    'mesonbuild/meson',
    'mesonbuild/wrapweb',
    'mesonbuild/meson-ci',
]


def get_wrapupdater():
    db = getattr(flask.g, '_wrapupdater', None)
    if db is None:
        dbdir = APP.config['DB_DIRECTORY']
        db = flask.g._wrapupdater = wrapupdater.WrapUpdater(dbdir)
    return db


def update_project(project, repo_url, branch):
    if branch == 'master':
        return jsonstatus.error(406, 'Will not update master branch')
    # FIXME, should launch in the background instead. This will now block
    # until branching is finished.
    try:
        get_wrapupdater().update_db(project, repo_url, branch)
        return jsonstatus.ok()
    except Exception as e:
        return jsonstatus.error(500, 'Wrap generation failed. %s' % e)


def github_pull_request():
    d = flask.request.get_json()
    base = d['pull_request']['base']
    full_repo_name = base['repo']['full_name']
    if not full_repo_name.startswith('mesonbuild/'):
        return jsonstatus.error(406, 'Not a mesonbuild project')
    if full_repo_name in RESTRICTED_PROJECTS:
        return jsonstatus.error(406, "We don't run hook for "
                                "restricted project names")
    if d['action'] == 'closed' and d['pull_request']['merged']:
        return update_project(project=base['repo']['name'],
                              repo_url=base['repo']['clone_url'],
                              branch=base['ref'])
    else:
        APP.logger.warning(flask.request.data)
        return jsonstatus.error(
            417, 'We got hook which is not merged pull request')


@APP.route('/github-hook', methods=['POST'])
def github_hook():
    headers = flask.request.headers
    if not headers.get('User-Agent').startswith('GitHub-Hookshot/'):
        return jsonstatus.error(401, 'Not a GitHub hook')
    signature = ('sha1=%s' %
                 hmac.new(APP.config['SECRET_KEY'].encode('utf-8'),
                          flask.request.data, hashlib.sha1).hexdigest())
    if headers.get('X-Hub-Signature') != signature:
        return jsonstatus.error(401, 'Not a valid secret key')
    if headers.get('X-Github-Event') == 'pull_request':
        return github_pull_request()
    else:
        return jsonstatus.error(405, 'Not a Pull Request hook')

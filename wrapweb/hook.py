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

from wrapweb.app import APP
from wrapweb import db


RESTRICTED_PROJECTS = ['mesonbuild/meson', 'mesonbuild/wrapweb', 'mesonbuild/meson-ci']


@APP.route('/github-hook', methods=['POST'])
def github_hook():
    if not flask.request.headers.get('User-Agent').startswith('GitHub-Hookshot/'):
        jsonout = flask.jsonify({'output': 'notok', 'error': 'Not a GitHub hook'})
        jsonout.status_code = 401
        return jsonout
    signature = 'sha1=%s' % hmac.new(APP.config['SECRET_KEY'].encode('utf-8'),
                                     flask.request.data, hashlib.sha1).hexdigest()
    if flask.request.headers.get('X-Hub-Signature') != signature:
        jsonout = flask.jsonify({'output': 'notok', 'error': 'Not a valid secret key'})
        jsonout.status_code = 401
        return jsonout
    if flask.request.headers.get('X-Github-Event') != 'pull_request':
        jsonout = flask.jsonify({'output': 'notok', 'error': 'Not a Pull Request hook'})
        jsonout.status_code = 405
        return jsonout
    d = flask.request.get_json()
    base = d['pull_request']['base']
    if not base['repo']['full_name'].startswith('mesonbuild/'):
        jsonout = flask.jsonify({'output': 'notok', 'error': 'Not a mesonbuild project'})
        jsonout.status_code = 406
        return jsonout
    if base['repo']['full_name'] in RESTRICTED_PROJECTS:
        jsonout = flask.jsonify({'output': 'notok',
                                 'error': "We don't run hook for restricted project names"})
        jsonout.status_code = 406
        return jsonout
    if d['action'] == 'closed' and d['pull_request']['merged']:
        project = base['repo']['name']
        branch = base['ref']
        repo_url = base['repo']['clone_url']
        if branch == 'master':
            out = {'output': 'notok', 'error': 'No bananas for you'}
            httpcode = 406
        else:
            out = {'output': 'ok'}
            httpcode = 200
            db_updater = db.get_update_db()
            # FIXME, should launch in the background instead. This will now block
            # until branching is finished.
            try:
                db_updater.update_db(project, repo_url, branch)
            except Exception as e:
                out = {'output': 'notok', 'error': 'Wrap generation failed. %s' % e}
                httpcode = 500
    else:
        APP.logger.warning(flask.request.data)
        out = {'output': 'notok', 'error': 'We got hook which is not merged pull request'}
        httpcode = 417

    jsonout = flask.jsonify(out)
    jsonout.status_code = httpcode
    return jsonout

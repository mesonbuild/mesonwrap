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
import github

from mesonwrap import githubdb
from wrapweb import flaskutil
from wrapweb import jsonstatus

BP = flask.Blueprint('api', __name__)


@flaskutil.appcontext_var(BP)
def _database():
    gh = github.Github(flask.current_app.config['GITHUB_TOKEN'])
    return githubdb.GithubDB(gh)


@_database.teardown
def _close_connection(db):
    db.close()


@BP.route('/v1/query/byname/<project>', methods=['GET'])
def name_query(project):
    return jsonstatus.ok(projects=_database().name_search(project))


@BP.route('/v1/query/get_latest/<project>', methods=['GET'])
def get_latest(project):
    latest = _database().get_latest_version(project)
    if latest is None:
        return jsonstatus.error(404, 'No such project')
    return jsonstatus.ok(branch=latest[0], revision=latest[1])


@BP.route('/v1/projects')
def get_projectlist():
    return jsonstatus.ok(projects=_database().name_search(''))


@BP.route('/v1/projects/<project>')
def get_project_info(project):
    metadata = _database().get_metadata(project)
    matches = _database().get_versions(project)
    if not matches:
        projects = _database().name_search(project)
        if project not in projects:
            return jsonstatus.error(404, 'No such project')
        return jsonstatus.ok(versions=[])
    md = dict()
    if metadata is not None:
        for field in ['homepage', 'description']:
            if metadata.has(field):
                md[field] = getattr(metadata, field)
    versions = [{'branch': i[0], 'revision': i[1]} for i in matches]
    return jsonstatus.ok(name=project, metadata=md, versions=versions)


@BP.route('/v1/projects/<project>/<branch>/<int:revision>/get_wrap')
def get_wrap(project, branch, revision):
    result = _database().get_wrap(project, branch, revision)
    if result is None:
        return jsonstatus.error(404, 'No such entry')
    resp = flask.make_response(result)
    resp.mimetype = 'text/plain'
    return resp


@BP.route('/v1/projects/<project>/<branch>/<int:revision>/get_zip')
def get_zip(project, branch, revision):
    result = _database().get_zip(project, branch, revision)
    if result is None:
        return jsonstatus.error(404, 'No such entry')
    resp = flask.make_response(result)
    resp.mimetype = 'application/zip'
    resp.headers['Content-Disposition'] = (
        f'attachment; filename={project}-{branch}-{revision}-wrap.zip')
    return resp

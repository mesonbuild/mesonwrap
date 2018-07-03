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

from mesonwrap import wrapdb
from wrapweb.app import APP
from wrapweb import jsonstatus


def get_query_db():
    db = getattr(flask.g, '_query_database', None)
    if db is None:
        dbdir = APP.config['DB_DIRECTORY']
        db = flask.g._query_database = wrapdb.WrapDatabase(dbdir)
    return db


@APP.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_query_database', None)
    if db is not None:
        db.close()


def get_projectlist():
    return jsonstatus.ok(projects=get_query_db().name_search(''))


@APP.route('/v1/query/byname/<project>', methods=['GET'])
def name_query(project):
    return jsonstatus.ok(projects=get_query_db().name_search(project))


@APP.route('/v1/query/get_latest/<project>', methods=['GET'])
def get_latest(project):
    matches = get_query_db().get_versions(project, latest=True)
    if len(matches) == 0:
        return jsonstatus.error(500, 'No such project')
    latest = matches[0]
    return jsonstatus.ok(branch=latest[0], revision=latest[1])


@APP.route('/v1/projects', defaults={'project': None})
@APP.route('/v1/projects/<project>')
def get_project_info(project):
    if project is None:
        return get_projectlist()
    matches = get_query_db().get_versions(project)
    if len(matches) == 0:
        return jsonstatus.error(500, 'No such project')
    versions = [{'branch': i[0], 'revision': i[1]} for i in matches]
    return jsonstatus.ok(versions=versions)


@APP.route('/v1/projects/<project>/<branch>/<int:revision>/get_wrap')
def get_wrap(project, branch, revision):
    result = get_query_db().get_wrap(project, branch, revision)
    if result is None:
        return jsonstatus.error(500, 'No such entry')
    resp = flask.make_response(result)
    resp.mimetype = 'text/plain'
    return resp


@APP.route('/v1/projects/<project>/<branch>/<int:revision>/get_zip')
def get_zip(project, branch, revision):
    result = get_query_db().get_zip(project, branch, revision)
    if result is None:
        return jsonstatus.error(500, 'No such entry')
    resp = flask.make_response(result)
    resp.mimetype = 'application/zip'
    resp.headers['Content-Disposition'] = (
        'attachment; filename=%s-%s-%d-wrap.zip' %
        (project, branch, revision))
    return resp

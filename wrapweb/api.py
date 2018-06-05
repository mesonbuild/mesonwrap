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


def get_query_db():
    db = getattr(flask.g, '_query_database', None)
    if db is None:
        dbdir = APP.config['DB_DIRECTORY']
        db = flask.g._query_database = wrapdb.WrapDatabase(dbdir)
    return db


def get_projectlist():
    querydb = get_query_db()
    res = {'output': 'ok', 'projects': querydb.name_search('')}
    return flask.jsonify(res)


@APP.route('/v1/query/byname/<project>', methods=['GET'])
def name_query(project):
    querydb = get_query_db()
    res = {'output': 'ok', 'projects': querydb.name_search(project)}
    return flask.jsonify(res)


@APP.route('/v1/query/get_latest/<project>', methods=['GET'])
def get_latest(project):
    querydb = get_query_db()
    matches = querydb.get_versions(project, latest=True)

    if len(matches) == 0:
        out = {'output': 'notok', 'error': 'No such project'}
        jsonout = flask.jsonify(out)
        jsonout.status_code = 500
        return jsonout

    latest = matches[0]
    out = {'output': 'ok', 'branch': latest[0], 'revision': latest[1]}
    jsonout = flask.jsonify(out)
    jsonout.status_code = 200
    return jsonout


@APP.route('/v1/projects', defaults={'project': None})
@APP.route('/v1/projects/<project>')
def get_project_info(project):
    if project is None:
        return get_projectlist()
    querydb = get_query_db()
    matches = querydb.get_versions(project)

    if len(matches) == 0:
        out = {'output': 'notok', 'error': 'No such project'}
        jsonout = flask.jsonify(out)
        jsonout.status_code = 500
        return jsonout

    out = {'output': 'ok', 'versions': []}
    for i in matches:
        e = {'branch': i[0], 'revision': i[1]}
        out['versions'].append(e)
    jsonout = flask.jsonify(out)
    jsonout.status_code = 200
    return jsonout


@APP.route('/v1/projects/<project>/<branch>/<int:revision>/get_wrap')
@APP.route('/v1/projects/<project>/<branch>/<int:revision>/get_zip')
def get_wrap(project, branch, revision):
    querydb = get_query_db()
    revision = revision
    if flask.request.path.endswith('/get_wrap'):
        result = querydb.get_wrap(project, branch, revision)
        mtype = 'text/plain'
        fname = ''
    else:
        result = querydb.get_zip(project, branch, revision)
        mtype = 'application/zip'
        fname = '%s-%s-%d-wrap.zip' % (project, branch, revision)
    if result is None:
        out = {'output': 'notok', 'error': 'No such entry'}
        jsonout = flask.jsonify(out)
        jsonout.status_code = 500
        return jsonout
    else:
        resp = flask.make_response(result)
        resp.mimetype = mtype
        if fname:
            resp.headers['Content-Disposition'] = (
                'attachment; filename=%s' % fname)
        return resp

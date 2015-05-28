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

from flask import Flask, jsonify, request, Response, g
import re, os
import wrapdb, wrapupdater

app = Flask(__name__)

db_directory = os.path.normpath(os.path.join(os.path.split(__file__)[0], '..'))

def get_query_db():
    db = getattr(g, '_query_database', None)
    if db is None:
        db = g._query_database = wrapdb.WrapDatabase(db_directory)
    return db

def get_update_db():
    db = getattr(g, '_update_database', None)
    if db is None:
        db = g._update_database = wrapupdater.WrapUpdater(db_directory)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_query_database', None)
    if db is not None:
        db.close()
    db = getattr(g, '_update_database', None)
    if db is not None:
        db.close()

def get_projectlist():
    querydb = get_query_db()
    res = {'output' : 'ok', 'projects' : querydb.name_search('')}
    return jsonify(res)

@app.route("/v1/projects", defaults={"project": None})
@app.route("/v1/projects/<project>")
def get_project_info(project):
    if project is None:
        return get_projectlist()
    querydb = get_query_db()
    matches = querydb.get_versions(project)

    if len(matches) == 0:
        out = {"output": "notok", "error": 'No such project'}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout

    out = {"output": "ok", "versions": []}
    for i in matches:
        e = {'branch': i[0], 'revision' : i[1]}
        out['versions'].append(e)
    jsonout = jsonify(out)
    jsonout.status_code = 200
    return jsonout

@app.route("/v1/projects/<project>/<branch>/<revision>/get_wrap")
@app.route("/v1/projects/<project>/<branch>/<revision>/get_zip")
def get_wrap(project, branch, revision):
    querydb = get_query_db()
    revision=int(revision)
    if request.path.endswith("/get_wrap"):
        result = querydb.get_wrap(project, branch, revision)
        mtype = 'text/plain'
    else:
        result = querydb.get_zip(project, branch, revision)
        mtype = 'application/zip'
    if result is None:
        out = {"output": "notok", "error": "No such entry"}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout
    else:
        return Response(result, mimetype=mtype)

@app.route("/github-pr", methods=["POST"])
def github_pr():
    d = request.data
    if d["action"] == "closed" and d["merged"] == True:
        project = d["repository"]["name"]
        branch = d["head"]["ref"]
        repo_url = d["head"]["clone_url"]
        if branch == "master":
            out = {"output": "notok", "error": "No bananas for you"}
            httpcode = 500
        else:
            out = {"output": "ok"}
            httpcode = 200
        db_updater = get_update_db()
        # FIXME, should launch in the background instead. This will now block
        # until branching is finished.
        try:
            db_updater.update_db(project, repo_url, branch)
        except Exception:
            out = {"output": "notok", "error": "Wrap generation failed."}
            httpcode = 500
    else:
        app.logger.warning(request.data)
        out = {"output": "notok", "error": "We got hook which is not merged pull request"}
        httpcode = 500

    jsonout = jsonify(out)
    jsonout.status_code = httpcode
    return jsonout

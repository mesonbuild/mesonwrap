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

from flask import Flask, jsonify, request, Response
import re
import wrapdb

app = Flask(__name__)

db_directory = '/tmp'
querydb = wrapdb.WrapDatabase(db_directory)
db_updater = wrapmanager.WrapManager(db_directory)

@app.route("/projects/<project>")
def get_project(project):
    out = {"output": "ok", "versions": []}
    for prj in db.get_versions(project):
        out["versions"].append(prj.to_dict())
    httpcode = 200

    jsonout = jsonify(out)
    jsonout.status_code = httpcode
    return jsonout

@app.route("/projects/<project>/get_wrap", methods=['GET'])
@app.route("/projects/<project>/get_zip", methods=['GET'])
def get_wrap(project):
    branch=request.args["branch"]
    revision=int(request.args["revision"])
    if request.path.endswith("/get_wrap"):
        result = db.get_wrap(project, branch, revision)
        mtype = 'text/plain'
    else:
        result = db.get_zip(project, branch, revision)
        mtype = 'application/zip'
    if result is None:
        out = {"output": "notok", "error": "No such entry"}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout
    else:
        return Response(result, mimetype=mtype)

# Change to match whatever github expects to get. Also verify password/IP/whatever.
@app.route('/update/<project>/<branch>')
def update_project(project, branch):
    if not re.fullmatch('[a-z0-9._]', project):
        out = {"output": "notok", "error": "Invalid project name"}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout
    if not re.fullmatch('[a-z0-9._]', branch):
        out = {"output": "notok", "error": "Invalid branch name"}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout
    # FIXME, should launch in the background instead. This will now block
    # until branching is finished.
    try:
        db_updater.update(project, branch)
    except Exception:
        out = {"output": "notok", "error": "Wrap generation failed."}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout
    return jsonify({'output': 'ok'})

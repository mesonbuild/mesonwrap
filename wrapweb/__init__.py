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
import wrapdb

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = wrapdb.WrapDatabase('/tmp')

from wrapweb.models import *

@app.route("/projects", defaults={"project": None})
@app.route("/projects/<project>")
def get_project(project=''):
    out = {"output": "ok", "projects": []}
    for prj in db.name_search(project):
        out["projects"].append(prj.to_dict())
    httpcode = 200

    jsonout = jsonify(out)
    jsonout.status_code = httpcode
    return jsonout

@app.route("/projects/<project>/get_wrap", methods=['GET'])
def get_wrap(project):
    branch=request.args["branch"]
    revision=int(request.args["revision"])
    result = db.get_wrap(project, branch, revision)
    if result is None:
        out = {"output": "notok", "error": "No such entry"}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout
    else:
        return Response(result, mimetype="text/plain")

@app.route("/projects/<project>/get_zip", methods=['GET'])
def get_wrap(project):
    branch=request.args["branch"]
    revision=int(request.args["revision"])
    result = db.get_zip(project, branch, revision)
    if result is None:
        out = {"output": "notok", "error": "No such entry"}
        jsonout = jsonify(out)
        jsonout.status_code = 500
        return jsonout
    else:
        return Response(result, mimetype="application/zip")

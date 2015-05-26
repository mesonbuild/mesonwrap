from flask import Flask, jsonify, request, Response
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

from wrapweb.models import *

@app.route("/projects", defaults={"project": None})
@app.route("/projects/<project>")
def get_project(project=None):
    if project is not None:
        prj = Project.query.filter_by(name=project).first()
        if prj:
            out = {"output": "ok"}
            out.update(prj.to_dict())
            httpcode = 200
        else:
            out = {"output": "notok", "error": "No such project"}
            httpcode = 500
    else:
        out = {"projects": []}
        for prj in Project.query.all():
            out["projects"].append(prj.to_dict())
        httpcode = 200

    jsonout = jsonify(out)
    jsonout.status_code = httpcode
    return jsonout

@app.route("/projects/<project>/get_wrap", methods=['GET'])
@app.route("/projects/<project>/get_zip", methods=['GET'])
def get_wrap(project):
    prj = Project.query.filter_by(name=project).first()
    if prj:
        if "branch" in request.args:
            wrap = Wrap.query.filter_by(
                branch=request.args["branch"],
                project_id=prj.id)
            if "revision" in request.args:
                wrap = wrap.filter_by(revision=request.args["revision"])
            wrap = wrap.first()
            if wrap is not None:
                if request.path.endswith("/get_wrap"):
                    return Response(wrap.wrapfile, mimetype="text/plain")
                elif request.path.endswith("/get_zip"):
                    return Response(wrap.tarball, mimetype="application/zip")
            else:
                out = {"output": "notok", "error": "No such branch or revision"}
        else:
            out = {"output": "notok", "error": "branch cannot be blank"}
    else:
        out = {"output": "notok", "error": "No such project"}

    jsonout = jsonify(out)
    jsonout.status_code = 500
    return jsonout

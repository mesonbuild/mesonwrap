from flask import Flask, jsonify, request, Response
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True)

    wraps = db.relationship("Wrap", backref="project",
                            lazy="dynamic")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Project %r>" % self.name

    def to_dict(self):
        out = {"name": self.name, "wraps" : []}
        for wrap in self.wraps:
            out["wraps"].append(wrap.to_dict())
        return out

class Wrap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(20))
    revision = db.Column(db.Integer)
    wrapfile = db.Column(db.Text)
    tarball = db.Column(db.LargeBinary)

    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))

    def __init__(self, branch, revision, wrapfile, tarball):
        self.branch = branch
        self.revision = revision
        self.wrapfile = wrapfile
        self.tarball = tarball

    def __repr__(self):
        return '<Post branch:%r revision:%r>' % (self.branch, self.revision)

    def to_dict(self):
        return {"branch": self.branch, "revision": self.revision}

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

if __name__ == "__main__":
    app.run(debug=True)

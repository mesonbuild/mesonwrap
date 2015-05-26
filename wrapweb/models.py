from wrapweb import db

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

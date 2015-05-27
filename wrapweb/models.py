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
    branch = db.Column(db.String(20), nullable=False)
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

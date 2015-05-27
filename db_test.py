#!/usr/bin/env python3
from wrapweb import db
from wrapweb.models import Project, Wrap

zlib_proj = Project("zlib")
zlib_wrap1 = Wrap("1.2.8", 1, "project('zlib')", b"rev1")
zlib_wrap2 = Wrap("1.2.8", 2, "project('zlib')", b"rev2")
zlib_proj.wraps.extend([zlib_wrap1, zlib_wrap2])
db.session.add(zlib_proj)
db.session.add(zlib_wrap1)
db.session.add(zlib_wrap2)

db.session.commit()

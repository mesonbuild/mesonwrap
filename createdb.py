#!/usr/bin/env python3
from wrapdb import app, db

db.drop_all()
db.create_all()

from mod_python import apache
from mod_python import util

import os
import wrapdb

def get_wrap(req, db):
    req.content_type = "text/plain"
    args = util.parse_qs(req.args)
    txt = db.get_wrap(args['package'][0], args['branch'][0], int(args['revision'][0]))
    req.write(txt)
    return apache.OK

def get_zip(req, db):
    req.content_type = "application/zip"
    args = util.parse_qs(req.args)
    txt = db.get_zip(args['package'][0], args['branch'][0], int(args['revision'][0]))
    req.write(txt)
    return apache.OK

def handler(req):
    action = os.path.split(req.filename)[-1]
    db = wrapdb.WrapDatabase('/var/www/html/wrapdb')
    if action == 'get_wrap.py':
        return get_wrap(req, db)
    elif action == 'get_zip.py':
        return get_zip(req, db)
    return apache.HTTP_NOT_FOUND
from mod_python import apache
from mod_python import util

import wrapdb

def handler(req):
    req.content_type = "text/plain"
    args = util.parse_qs(req.args)
    db = wrapdb.WrapDatabase('/var/www/html/wrapdb')
    txt = db.get_wrap(args['package'][0], args['branch'][0], int(args['revision'][0]))
    req.write(txt)
    return apache.OK

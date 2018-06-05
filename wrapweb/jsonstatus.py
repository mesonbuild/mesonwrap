import flask


def ok(**kwargs):
    jsonout = flask.jsonify(dict(output='ok', **kwargs))
    jsonout.status_code = 200
    return jsonout


def error(code, message):
    jsonout = flask.jsonify(dict(output='notok', error=message))
    jsonout.status_code = code
    return jsonout

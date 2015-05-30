import flask

# Create the application.
APP = flask.Flask(__name__)

APP.config.from_object("wrapweb.default_config")

@APP.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, "_query_database", None)
    if db is not None:
        db.close()
    db = getattr(flask.g, "_update_database", None)
    if db is not None:
        db.close()

# Finalize the import of other controllers
import wrapweb.api
import wrapweb.ui

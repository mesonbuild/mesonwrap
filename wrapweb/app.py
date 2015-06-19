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

import flask
import os

# Create the application.
APP = flask.Flask(__name__)

APP.config.from_object("wrapweb.default_config")
if "WRAPDB_CONFIG" in os.environ:
    APP.config.from_envvar("WRAPDB_CONFIG")

@APP.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, "_query_database", None)
    if db is not None:
        db.close()
    db = getattr(flask.g, "_update_database", None)
    if db is not None:
        db.close()

# Finalize the import of other controllers
# pylint: disable=unused-import
import wrapweb.api
import wrapweb.ui

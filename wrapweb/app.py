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

import os

import flask

from wrapweb import api
from wrapweb import jsonstatus
from wrapweb import ui


# Create the application.
APP = flask.Flask(__name__)

APP.config.from_object('wrapweb.default_config.Config')
if 'WRAPDB_CONFIG' in os.environ:
    APP.config.from_envvar('WRAPDB_CONFIG')

jsonstatus.init_app(APP)
APP.register_blueprint(api.BP)
APP.register_blueprint(ui.BP)

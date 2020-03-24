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

import json

import flask

from wrapweb import api

BP = flask.Blueprint('ui', __name__)


def response_to_json(resp):
    return json.loads(resp.get_data().decode('utf-8'))


@BP.route('/', methods=['GET'])
def index():
    return flask.render_template('projects.html')


@BP.route('/async/projects', methods=['GET'])
def async_projects():
    j = response_to_json(api.get_projectlist())
    return flask.render_template(
        'async_projects.html',
        projects=j['projects'])


@BP.route('/<project>', methods=['GET'])
def project_info(project):
    j = response_to_json(api.get_project_info(project))
    return flask.render_template(
        'project.html',
        project=project,
        resp=j)


@BP.route('/tickets', methods=['GET'])
def tickets():
    return flask.render_template('tickets.html')


@BP.route('/async/tickets', methods=['GET'])
def async_tickets():
    tickets = api._database().get_tickets()
    return flask.render_template(
        'async_tickets.html',
        tickets=tickets)


# This is called when user opens get_wrap handler and CSS override is not
# present.
@BP.route('/favicon.ico')
def favicon():
    return flask.current_app.send_static_file('ico/favicon.png')

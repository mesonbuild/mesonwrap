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

import collections
import json

import flask

from wrapweb import api, jsonstatus

BP = flask.Blueprint('ui', __name__)


def response_to_json(resp):
    return json.loads(resp.get_data().decode('utf-8'))


@BP.route('/', methods=['GET'])
def index():
    j = response_to_json(api.get_projectlist())
    return flask.render_template(
        'projects.html',
        projects=j['projects'])


@BP.route('/<project>', methods=['GET'])
def project_info(project):
    j = response_to_json(api.get_project_info(project))
    return flask.render_template(
        'project.html',
        title='%s - Wrap DB' % project,
        project=project,
        resp=j)


Ticket = collections.namedtuple('Ticket', (
    'title',
    'project',
    'project_link',
    'issue_link',
    'type',  # wrapdb_issue, pull_request, wrap_issue
    'author',
    'author_link',
    'timestamp',
))


@BP.route('/tickets', methods=['GET'])
def tickets():
    # TODO(legeana): implement this
    tickets = [
        Ticket(title='New wrap blah',
               project='wrapdb',
               project_link='https://github.com/mesonbuild/wrapdb',
               issue_link='http://example.com',
               type='wrapdb_issue',
               author='someuser',
               author_link='https://github.com/legeana',
               timestamp='yesterday'),
        Ticket(title='New version',
               project='somewrap',
               project_link='https://github.com/mesonbuild/somewrap',
               issue_link='http://example.com',
               type='pull_request',
               author='otheruser',
               author_link='https://github.com/legeana',
               timestamp='19:00 17-06-2013'),
        Ticket(title="It doesn't work T_T",
               project='otherwrap-and-its-looong',
               project_link='https://github.com/mesonbuild/otherwrap',
               issue_link='http://example.com',
               type='wrap_issue',
               author='saduser',
               author_link='https://github.com/legeana',
               timestamp='some time ago'),
    ]
    return flask.render_template(
        'tickets.html',
        title='Tickets - Wrap DB',
        tickets=tickets)


# This is called when user opens get_wrap handler and CSS override is not
# present.
@BP.route('/favicon.ico')
def favicon():
    return jsonstatus.error(404, 'Favicon not found')

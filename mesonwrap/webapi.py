import abc
import hashlib
import hmac
import json
from typing import Any, Dict
import urllib.error
import urllib.parse
import urllib.request

from mesonwrap import wrap


JSON = Dict[Any, Any]


class ServerError(Exception):
    pass


class APIError(ServerError):
    pass


class AbstractHTTPClient(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def fetch(self, url: str) -> bytes:
        pass

    @abc.abstractmethod
    def post(
        self, url: str, content_type: str, headers: Dict[str, str], data: bytes
    ) -> bytes:
        pass


class _HTTPClient(AbstractHTTPClient):

    def __init__(self, url: str):
        self.url = url

    def fetch(self, url: str) -> bytes:
        with urllib.request.urlopen(self.url + url) as r:
            return r.read()

    def post(
        self, url: str, content_type: str, headers: Dict[str, str], data: bytes
    ) -> bytes:
        headers = headers.copy()
        headers['Content-Type'] = content_type
        req = urllib.request.Request(self.url + '/github-hook', data, headers)
        with urllib.request.urlopen(req) as r:
            return r.read()


class _APIClient:

    def __init__(self, http_client: AbstractHTTPClient):
        self._http = http_client

    @staticmethod
    def _check_part(part, name):
        if '/' in part:
            raise ValueError("Invalid {}, '/' is not allowed".format(name))

    @classmethod
    def _check_project(cls, project):
        cls._check_part(project, 'project name')

    @classmethod
    def _check_version(cls, version):
        cls._check_part(version, 'version')

    @staticmethod
    def _check_revision(revision):
        if not isinstance(revision, int):
            raise ValueError('Invalid revision, '
                             'expected int, got {}'.format(type(revision)))

    def fetch(self, url: str) -> bytes:
        return self._http.fetch(url)

    def fetch_json(self, url: str) -> JSON:
        try:
            data = self.fetch(url)
        except urllib.request.HTTPError as e:
            if e.code != 404:
                raise ServerError('Server error: unknown error code',
                                  e.code, e.reason)
            data = e.read()
        return self.parse_json(data)

    def post_json(
        self, url: str, content_type: str, headers: Dict[str, str], data: bytes
    ) -> JSON:
        try:
            data = self._http.post(
                url=url, content_type=content_type,
                headers=headers, data=data)
        except urllib.request.HTTPError as e:
            data = e.read()
        return self.parse_json(data)

    def parse_json(self, data) -> JSON:
        if isinstance(data, bytes):
            data = data.decode('utf8')
        j = json.loads(data)
        if 'output' not in j:
            raise ValueError('Invalid server response: no output field')
        elif j['output'] == 'ok':
            return j
        elif j['output'] == 'notok':
            if 'error' not in j:
                raise ValueError('Invalid server response: no error field')
            raise APIError(j['error'])
        else:
            raise ValueError('Invalid server response: unknown output value',
                             j['output'])

    def query_v1_byname(self, project: str) -> JSON:
        return self.fetch_json('/v1/query/byname/' + project)

    def query_v1_get_latest(self, project: str) -> JSON:
        return self.fetch_json('/v1/query/get_latest/' + project)

    def fetch_v1_projects(self) -> JSON:
        return self.fetch_json('/v1/projects')

    def fetch_v1_project(self, project: str) -> JSON:
        self._check_part(project, 'project name')
        return self.fetch_json('/v1/projects/' + project)

    def fetch_v1_project_wrap(
        self, project: str, version: str, revision: int
    ) -> bytes:
        self._check_project(project)
        self._check_version(version)
        self._check_revision(revision)
        url = '/v1/projects/{project}/{version}/{revision}/get_wrap'
        return self.fetch(url.format(project=project,
                                     version=version,
                                     revision=revision))

    def fetch_v1_project_zip(
        self, project: str, version: str, revision: int
    ) -> bytes:
        self._check_project(project)
        self._check_version(version)
        self._check_revision(revision)
        url = '/v1/projects/{project}/{version}/{revision}/get_zip'
        return self.fetch(url.format(project=project,
                                     version=version,
                                     revision=revision))

    def pull_request_hook(self, js: JSON, secret: bytes) -> JSON:
        data = json.dumps(js).encode('utf8')
        signature = hmac.new(secret, data, hashlib.sha1).hexdigest()
        headers = {
            'User-Agent': 'GitHub-Hookshot/MesonWrap-Client',
            'X-Hub-Signature': 'sha1=' + signature,
            'X-Github-Event': 'pull_request',
        }
        return self.parse_json(self._http.post(
            '/github-hook',
            content_type='application/json',
            headers=headers,
            data=data))


class Revision:

    def __init__(self, api: _APIClient, project: 'Project',
                 version: 'Version', revision: int):
        self._api = api
        self.project = project
        self.version = version
        self.revision = revision
        self.__wrap = None
        self.__zip = None

    @property
    def wrap(self):
        if self.__wrap is None:
            self.__wrap = self._api.fetch_v1_project_wrap(self.project.name,
                                                          self.version.version,
                                                          self.revision)
        return self.__wrap

    @property
    def zip(self):
        if self.__zip is None:
            self.__zip = self._api.fetch_v1_project_zip(self.project.name,
                                                        self.version.version,
                                                        self.revision)
        return self.__zip

    @property
    def combined_wrap(self):
        return wrap.Wrap(name=self.version.project.name,
                         version=self.version.version,
                         revision=self.revision,
                         wrap=self.wrap,
                         zip=self.zip)


class Version:

    def __init__(self, api: _APIClient, project: 'Project', version: str):
        self._api = api
        self.project = project
        self.version = version
        self.__revisions_called = False
        self.__revisions = dict()

    @property
    def _revision_ids(self):
        return self.project._version_ids[self.version]

    @property
    def _latest(self):
        return max(self._revision_ids)

    def _get_revision(self, rev):
        if rev not in self.__revisions:
            self.__revisions[rev] = Revision(self._api, self.project, self,
                                             rev)
        return self.__revisions[rev]

    @property
    def revisions(self):
        if not self.__revisions_called:
            for rev in self._revision_ids:
                if rev not in self.__revisions:
                    self.__revisions[rev] = Revision(self._api, self.project,
                                                     self, rev)
            self.__revisions_called = True
        return self.__revisions

    @property
    def latest(self):
        return self.revisions[self._latest]


class Project:

    def __init__(self, api: _APIClient, name: str):
        self._api = api
        self.name = name
        self.__version_ids = None
        self.__versions_called = False
        self.__versions = dict()
        self.__latest = None

    @property
    def _version_ids(self):
        if self.__version_ids is None:
            js = self._api.fetch_v1_project(self.name)
            self.__version_ids = dict()
            for version in js['versions']:
                ver = version['branch']
                rev = int(version['revision'])
                if ver not in self.__version_ids:
                    self.__version_ids[ver] = set()
                self.__version_ids[ver].add(rev)
        return self.__version_ids

    def _get_version(self, ver):
        if ver not in self.__versions:
            self.__versions[ver] = Version(self._api, self, ver)
        return self.__versions[ver]

    @property
    def versions(self):
        if not self.__versions_called:
            for ver in self._version_ids.keys():
                self._get_version(ver)
            self.__versions_called = True
        return self.__versions

    def query_latest(self) -> Revision:
        if self.__latest is None:
            js = self._api.query_v1_get_latest(self.name)
            ver = js['branch']
            rev = js['revision']
            self.__latest = self._get_version(ver)._get_revision(rev)
        return self.__latest


class ProjectSet:

    def __init__(self, api):
        self._api = api
        self.__project_names = None
        self.__projects_called = False
        self.__projects = dict()

    @property
    def _project_names(self):
        if self.__project_names is None:
            self.__project_names = self._api.fetch_v1_projects()['projects']
        return self.__project_names

    def _get_project(self, name):
        if name not in self.__projects:
            self.__projects[name] = Project(self._api, name)
        return self.__projects[name]

    @property
    def _projects(self):
        if not self.__projects_called:
            for name in self._project_names:
                self._get_project(name)
            self.__projects_called = True
        return self.__projects

    def __contains__(self, item):
        return item in self._project_names

    def __len__(self):
        return len(self._project_names)

    def __getitem__(self, key):
        return self._projects[key]

    def __iter__(self):
        return iter(self._projects.values())

    def query_by_name_prefix(self, prefix: str) -> [Project]:
        js = self._api.query_v1_byname(prefix)
        return [self._get_project(name) for name in js['projects']]


class WebAPI:

    def __init__(
        self, url: str = None, http_client: AbstractHTTPClient = None
    ):
        """Initialize WebAPI.

        Args:
            url: base URL of the server.
            http_client: optional http_client object to be used
                         instead of the URL. url parameter is ignored.
                         Must implement AbstractHTTPClient.
        """
        if http_client is not None:
            self._api = _APIClient(http_client)
        elif url:
            self._api = _APIClient(_HTTPClient(url))
        else:
            raise ValueError('Must set url or http_client')

    def _get_project_names(self):
        return self._api.fetch_v1_projects()['projects']

    def projects(self):
        """Returns new version of ProjectSet.

           All operations on ProjectSet are cached.
        """
        return ProjectSet(self._api)

    def ping(self):
        """Returns True if able to connect."""
        try:
            self._api.fetch('/')
            return True
        except urllib.error.URLError:
            return False

    def pull_request_hook(self, organization, project, branch, clone_url):
        repo = dict(full_name='{}/{}'.format(organization, project),
                    name=project,
                    clone_url=clone_url)
        base = dict(repo=repo, ref=branch)
        js = dict(pull_request=dict(base=base, merged=True),
                  action='closed')
        # FIXME let user set the key
        return self._api.pull_request_hook(js, b'changeme please')

import abc
from typing import Any, Dict, List, Optional

import requests

from mesonwrap import wrap
from mesonwrap import upstream


JSON = Dict[Any, Any]


class ServerError(Exception):
    pass


class APIError(ServerError):
    pass


class AbstractHTTPResponse(metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def status_code(self) -> bool: ...

    @abc.abstractproperty
    def reason(self) -> str: ...

    @abc.abstractmethod
    def __bool__(self) -> bool: ...

    @abc.abstractproperty
    def content(self) -> bytes: ...

    @abc.abstractproperty
    def text(self) -> str: ...

    @abc.abstractmethod
    def json(self, **kwargs) -> JSON: ...


AbstractHTTPResponse.register(requests.Response)


class AbstractHTTPClient(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get(self, url: str) -> AbstractHTTPResponse:
        pass


class _HTTPClient(AbstractHTTPClient):

    def __init__(self, url: str):
        self.url = url

    def get(self, url: str) -> AbstractHTTPResponse:
        with requests.get(self.url + url) as rv:
            _ = rv.content  # read the content before the connection is closed
            return rv


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
        rv = self._http.get(url)
        if not rv:
            if rv.status_code >= 500:
                raise ServerError('Server error', rv.status_code, rv.reason)
            raise APIError(rv.status_code, rv.reason)
        return rv.content

    def fetch_json(self, url: str) -> JSON:
        return self.interpret(self._http.get(url))

    @staticmethod
    def interpret(rv: AbstractHTTPResponse) -> JSON:
        if not rv and rv.status_code >= 500:
            raise ServerError('Server error', rv.status_code, rv.reason)
        j = rv.json()
        if 'output' not in j:
            raise ValueError('Invalid server response: no output field')
        if j['output'] == 'ok':
            return j
        if j['output'] == 'notok':
            if 'error' not in j:
                raise ValueError('Invalid server response: no error field')
            raise APIError(j['error'])
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


class Revision:

    def __init__(self, api: _APIClient, project: 'Project',
                 version: 'Version', revision: int):
        self._api = api
        self.project = project
        self.version = version
        self.revision = revision
        self.__wrapfile_content = None
        self.__zip = None

    @property
    def wrapfile_content(self) -> str:
        if self.__wrapfile_content is None:
            data = self._api.fetch_v1_project_wrap(self.project.name,
                                                   self.version.version,
                                                   self.revision)
            self.__wrapfile_content = data.decode('utf-8')
        return self.__wrapfile_content

    @property
    def wrapfile(self) -> upstream.WrapFile:
        return upstream.WrapFile.from_string(self.wrapfile_content)

    @property
    def zip(self) -> bytes:
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
                         wrapfile_content=self.wrapfile_content,
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
            for ver in self._version_ids:
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

    def query_by_name_prefix(self, prefix: str) -> List[Project]:
        js = self._api.query_v1_byname(prefix)
        return [self._get_project(name) for name in js['projects']]

    def query_by_name(self, name: str) -> Optional[Project]:
        js = self._api.query_v1_byname(name)  # FIXME this can be optimized
        if name not in js['projects']:
            return None
        return self._get_project(name)


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

    def ping(self) -> bool:
        """Returns True if able to connect."""
        try:
            return bool(self._api.fetch('/'))
        except OSError:
            return False

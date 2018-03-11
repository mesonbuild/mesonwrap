import json
import urllib.request
import urllib.error


class ServerError(Exception):
    pass


class _APIClient:

    def __init__(self, url):
        self.url = url

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
            raise ValueError('Invalid revision, expected int, got {}'.format(type(revision)))

    def fetch(self, url):
        with urllib.request.urlopen(self.url + url) as r:
            return r.read()

    def fetch_json(self, url):
        j = json.loads(self.fetch(url).decode('utf8'))
        if j['output'] == 'ok':
            return j
        elif j['output'] == 'notok':
            raise ServerError('Server error')
        else:
            raise ValueError('Invalid server response')

    def fetch_v1_projects(self):
        return self.fetch_json('/v1/projects')

    def fetch_v1_project(self, project: str):
        self._check_part(project, 'project name')
        return self.fetch_json('/v1/projects/' + project)

    def fetch_v1_project_wrap(self, project: str, version: str, revision: int):
        self._check_project(project)
        self._check_version(version)
        self._check_revision(revision)
        return self.fetch('/v1/projects/{project}/{version}/{revision}/get_wrap'.format(
            project=project, version=version, revision=revision))

    def fetch_v1_project_zip(self, project: str, version: str, revision: str):
        self._check_project(project)
        self._check_version(version)
        self._check_revision(revision)
        return self.fetch('/v1/projects/{project}/{version}/{revision}/get_zip'.format(
            project=project, version=version, revision=revision))


class Revision:

    def __init__(self, api: _APIClient, project: 'Project', version: 'Version', revision: int):
        self.project = project
        self.version = version
        self.revision = revision
        self.__wrap = None
        self.__zip = None

    @property
    def wrap(self):
        if self.__wrap is None:
            self.__wrap = self._api.fetch_v1_project_wrap(self.project, self.version, self.revision)
        return self.__wrap

    @property
    def zip(self):
        if self.__zip is None:
            self.__zip = self._api.fetch_v1_project_zip(self.project, self.version, self.revision)
        return self.__zip


class Version:

    def __init__(self, api: _APIClient, project: 'Project', version: str, revisions: [int]):
        self._api = api
        self.project = project
        self.version = version
        self._revision_ids = revisions
        self._latest = max(self._revision_ids)
        self.__revisions = None

    @property
    def revisions(self):
        if self.__revisions is None:
            self.__revisions = dict()
            for rev in self._revision_ids:
                self.__revisions[rev] = Revision(self._api, self.project, self, rev)
        return self.__revisions

    @property
    def latest(self):
        return self.revisions[self._latest]


class Project:

    def __init__(self, api: _APIClient, name: str):
        self._api = api
        self.name = name
        self.__version_ids = None
        self.__versions = None

    @property
    def _version_ids(self):
        if self.__version_ids is None:
            js = self._api.fetch_v1_project(self.name)
            self.__version_ids = dict()
            for version in js['versions']:
                ver = version['branch']
                rev = int(version['revision'])
                if ver not in self.__version_ids:
                    self.__version_ids[ver] = list()
                self.__version_ids[ver].append(rev)
        return self.__version_ids

    @property
    def versions(self):
        if self.__versions is None:
            self.__versions = dict()
            for ver, revs in self._version_ids.items():
                self.__versions[ver] = Version(self._api, self, ver, revs)
        return self.__versions


class ProjectSet:

    def __init__(self, api):
        self._api = api
        self.__project_names = None
        self.__projects = None

    @property
    def _project_names(self):
        if self.__project_names is None:
            self.__project_names = self._api.fetch_v1_projects()['projects']
        return self.__project_names

    @property
    def _projects(self):
        if self.__projects is None:
            self.__projects = [Project(self._api, name) for name in self._project_names]
        return self.__projects

    def __contains__(self, item):
        return item in self._project_names

    def __len__(self):
        return len(self._project_names)

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return Project(self._api, key)

    def __iter__(self):
        return iter(self._projects)


class WebAPI:

    def __init__(self, url):
        self._api = _APIClient(url)

    def _get_project_names(self):
        return self._api.fetch_v1_projects()['projects']

    def projects(self):
        '''Returns new version of ProjectSet, all operations on ProjectSet are cached.'''
        return ProjectSet(self._api)

    def ping(self):
        '''Returns True if able to connect'''
        try:
            self._api.fetch('/')
            return True
        except urllib.error.URLError:
            return False

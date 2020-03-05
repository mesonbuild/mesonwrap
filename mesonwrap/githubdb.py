import collections
import logging
import threading
from typing import Iterable, List, Optional, Tuple

import cachetools
import github
import requests

from mesonwrap import inventory
from mesonwrap import version


UPSTREAM_WRAP_LABEL = 'upstream.wrap'
PATCH_ZIP_LABEL = 'patch.zip'
CACHE_SIZE = 1000
CACHE_TTL = 30 * 60  # 30 minutes
TICKETS_TTL = 5 * 60 # 5 minutes


Version = Tuple[str, int]


class Organization:

    def __init__(self, pygithub: github.Github,
                 organization: str = 'mesonbuild'):
        assert isinstance(pygithub, github.Github)
        assert isinstance(organization, str)
        self._gh = pygithub
        self._org = organization

    def __call__(self):
        return self._gh.get_organization(self._org)

    @property
    def github(self):
        return self._gh


class LockedCache:

    def __init__(self, cache: cachetools.Cache):
        self.lock = threading.Lock()
        self.cache = cache

    def __call__(self, **kwargs):
        return cachetools.cached(cache=self.cache, lock=self.lock, **kwargs)


# TODO type must be enum
Ticket = collections.namedtuple('Ticket', (
    'title',
    'project',
    'project_url',
    'issue_url',
    'type',  # wrapdb_issue, pull_request, wrap_issue
    'author',
    'author_url',
    'timestamp',
))


# global cache instances
_repo = LockedCache(cachetools.TTLCache(maxsize=1, ttl=CACHE_TTL))
_release = LockedCache(cachetools.TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL))
_asset = LockedCache(cachetools.LRUCache(maxsize=CACHE_SIZE))
_ticket = LockedCache(cachetools.TTLCache(maxsize=1, ttl=TICKETS_TTL))
_log = logging.getLogger(__name__)


def _cache_key(organization, *args, **kwargs):
    """Skip the first argument."""
    return cachetools.keys.hashkey(*args, **kwargs)


@_repo(key=_cache_key)
def _repository_list(org: Organization):
    return sorted([repo.name for repo in org().get_repos()
                   if inventory.is_wrap_project_name(repo.name)])


def _get_versions(org: Organization, project: str) -> Iterable[Version]:
    repo = org().get_repo(project)
    for release in repo.get_releases():
        dash = release.tag_name.rfind('-')
        if dash == -1:
            continue
        version = release.tag_name[:dash]
        revision = int(release.tag_name[dash + 1:])
        yield (version, revision)


@_release(key=_cache_key)
def _release_list(org: Organization, project: str) -> List[Version]:
    assert isinstance(project, str)
    iterator = _get_versions(org, project)
    return sorted(iterator, key=version.version_key, reverse=True)


@_asset(key=_cache_key)
def _asset(org: Organization,
           project: str, branch: str, revision: int, label: str) -> bytes:
    repo = org().get_repo(project)
    release = repo.get_release('{}-{}'.format(branch, revision))
    for asset in release.get_assets():
        if asset.label == label:
            with requests.get(asset.browser_download_url) as rv:
                rv.raise_for_status()
                return rv.content
    _log.error('Asset not found project=%s branch=%s revision=%d label=%s',
               project, branch, revision, label)
    raise KeyError('Asset not found', project, branch, revision, label)


def _get_wrap(org: Organization,
              project: str, branch: str, revision: int) -> Optional[str]:
    try:
        data = _asset(org, project, branch, revision, UPSTREAM_WRAP_LABEL)
        return data.decode('utf-8')
    except Exception as e:
        _log.error('get_wrap(%s, %s, %d): %s', project, branch, revision, e)
        return None


def _get_zip(org: Organization,
             project: str, branch: str, revision: int) -> Optional[bytes]:
    try:
        return _asset(org, project, branch, revision, PATCH_ZIP_LABEL)
    except Exception as e:
        _log.error('get_zip(%s, %s, %d): %s', project, branch, revision, e)
        return None


@_ticket(key=_cache_key)
def _tickets(org: Organization):
    restricted = ' '.join(
        '-repo:{}'.format(project)
        for project in inventory._RESTRICTED_ORG_PROJECTS
        if project != 'wrapdb'
    )
    query = 'org:mesonbuild is:open ' + restricted
    result = []
    for issue in org.github.search_issues(query):
        if issue.repository.name == 'wrapdb':
            ticket_type = 'wrapdb_issue'
        elif issue.pull_request:
            ticket_type = 'pull_request'
        else:
            ticket_type = 'wrap_issue'
        result.append(Ticket(
            title=issue.title,
            project=issue.repository.name,
            project_url=issue.repository.html_url,
            issue_url=issue.html_url,
            type=ticket_type,
            author=issue.user.login,
            author_url=issue.user.html_url,
            timestamp=str(issue.updated_at)))
    return sorted(result, key=lambda r: (r.project, r.issue_url))


# TODO implement caching
# https://developer.github.com/v3/#conditional-requests
# or just some cache with timeouts
class GithubDB:

    def __init__(self, pygithub: github.Github,
                 organization: str = 'mesonbuild'):
        self._org = Organization(pygithub, organization)

    def close(self):
        pass

    def insert(self,
               project: str,
               branch: str,
               revision: int,
               wrap: str,
               zip: bytes):
        raise NotImplementedError('Only read only access is supported')

    def name_search(self, text):
        return sorted([repo for repo in _repository_list(self._org)
                       if repo.startswith(text)])

    def get_versions(self, project: str) -> List[Version]:
        return _release_list(self._org, project)

    def get_latest_version(self, project) -> Optional[Version]:
        # get_latest_release() is not following semantic versioning
        results = self.get_versions(project)
        if not results:
            return None
        return results[0]

    # TODO consider redirect
    def get_wrap(self, project, branch, revision) -> Optional[str]:
        return _get_wrap(self._org, project, branch, revision)

    # TODO consider redirect
    def get_zip(self, project, branch, revision) -> Optional[bytes]:
        return _get_zip(self._org, project, branch, revision)

    def get_tickets(self) -> List[Ticket]:
        return _tickets(self._org)

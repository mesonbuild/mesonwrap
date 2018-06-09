from distutils import version
import github
import urllib.request

from mesonwrap import inventory


UPSTREAM_WRAP_LABEL = 'upstream.wrap'
PATCH_ZIP_LABEL = 'patch.zip'


# TODO implement caching
# https://developer.github.com/v3/#conditional-requests
# or just some cache with timeouts
class GithubDB:

    def __init__(self, pygithub: github.Github,
                 organization: str = 'mesonbuild'):
        assert isinstance(pygithub, github.Github)
        assert isinstance(organization, str)
        self._gh = pygithub
        self._org = organization

    def close(self):
        pass

    @property
    def _organization(self):
        return self._gh.get_organization(self._org)

    def insert(self,
               project: str,
               branch: str,
               revision: int,
               wrap: str,
               zip: bytes):
        raise NotImplementedError('Only read only access is supported')

    def name_search(self, text):
        return sorted([repo.name for repo in self._organization.get_repos()
                       if (inventory.is_wrap_project_name(repo.name) and
                           repo.name.startswith(text))])

    def _get_versions(self, project):
        repo = self._organization.get_repo(project)
        for release in repo.get_releases():
            dash = release.tag_name.rfind('-')
            if dash == -1:
                continue
            version = release.tag_name[:dash]
            revision = int(release.tag_name[dash + 1:])
            yield (version, revision)

    def get_versions(self, project, latest=False):
        if latest:
            # get_latest_release() is not following semantic versioning
            latest_ver = max((version.LooseVersion(r[0]), r[1])
                             for r in self._get_versions(project))
            return [(str(latest_ver[0]), latest_ver[1])]
        else:
            return list(self._get_versions(project))

    def _get_asset(self, label, project, branch, revision) -> bytes:
        try:
            repo = self._organization.get_repo(project)
            release = repo.get_release('{}-{}'.format(branch, revision))
            for asset in release.get_assets():
                if asset.label == label:
                    url = asset.browser_download_url
                    with urllib.request.urlopen(url) as a:
                        return a.read()
            # FIXME
            return None
        except Exception:
            return None

    # TODO consider redirect
    def get_wrap(self, project, branch, revision) -> str:
        return self._get_asset(UPSTREAM_WRAP_LABEL,
                               project, branch, revision).decode('utf-8')

    # TODO consider redirect
    def get_zip(self, project, branch, revision) -> bytes:
        return self._get_asset(PATCH_ZIP_LABEL, project, branch, revision)

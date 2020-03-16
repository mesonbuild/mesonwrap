from collections import defaultdict
import dataclasses
from typing import List, Optional, Tuple
import unittest
from unittest import mock

from wrapweb import APP
from wrapweb import api

Version = Tuple[str, int]


@dataclasses.dataclass
class FakeRelease:

    name: str
    version: str
    revision: int
    wrapfile_content: str
    zip: bytes


class FakeDatabase:

    def __init__(self):
        # Dict[Dict[Dict[FakeRelease]]]
        self._projects = defaultdict(lambda: defaultdict(dict))

    def add(self, name: str, version: str, revision: int) -> None:
        self._projects[name][version][revision] = (
            FakeRelease(name, version, revision))

    def close(self) -> None:
        pass

    def insert(self,
               project: str,
               version: str,
               revision: int,
               wrapfile_content: str,
               zip: bytes):
        self._projects[project][version][revision] = FakeRelease(
            project, version, revision, wrapfile_content, zip)

    def name_search(self, text: str) -> List[str]:
        return sorted([repo for repo in self._projects
                       if repo.startswith(text)])

    def get_versions(self, project: str) -> List[Version]:
        if project not in self._projects:
            raise KeyError(project)
        proj = self._projects[project]
        return [
            (release.version, release.revision)
            for version in proj.values()
            for release in version.values()
        ]

    def get_latest_version(self, project: str) -> Optional[Version]:
        # get_latest_release() is not following semantic versioning
        results = self.get_versions(project)
        if not results:
            return None
        return results[0]

    def get_wrap(self, project, branch, revision) -> Optional[str]:
        return self._projects[project][branch][revision].wrapfile_content

    def get_zip(self, project, branch, revision) -> Optional[bytes]:
        return self._projects[project][branch][revision].zip



class TestBase(unittest.TestCase):

    def _patch_object(self, module, name, *args, **kwargs):
        patcher = mock.patch.object(module, name, *args, **kwargs)
        obj = patcher.start()
        self.addCleanup(patcher.stop)
        return obj

    def setUp(self):
        super().setUp()
        APP.testing = True  # propagate exceptions
        self.database = FakeDatabase()
        self._patch_object(api, '_database', return_value=self.database)
        self.client = APP.test_client()
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

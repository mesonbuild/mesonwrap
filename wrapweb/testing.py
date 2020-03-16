from collections import defaultdict
import dataclasses
from typing import List, Optional, Tuple
import unittest
from unittest import mock

import flask

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

    def add(self, name: str, version: str, revision: int,
            wrapfile_content: str, zip: bytes) -> None:
        self._projects[name][version][revision] = (
            FakeRelease(name, version, revision,
                        wrapfile_content, zip))

    def close(self) -> None:
        pass

    def name_search(self, text: str) -> List[str]:
        return sorted([repo for repo in self._projects
                       if repo.startswith(text)])

    def get_versions(self, project: str) -> List[Version]:
        if project not in self._projects:
            return []
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

    BLUEPRINT = None

    def _patch_object(self, module, name, *args, **kwargs):
        patcher = mock.patch.object(module, name, *args, **kwargs)
        obj = patcher.start()
        self.addCleanup(patcher.stop)
        return obj

    def setUp(self):
        super().setUp()
        self.app = flask.Flask(__name__)
        self.app.register_blueprint(self.BLUEPRINT)
        self.app.testing = True  # propagate exceptions
        self.database = FakeDatabase()
        self._patch_object(api, '_database', return_value=self.database)
        self.client = self.app.test_client()
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def assertOk(self, rv):
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()['output'], 'ok')

    def assertNotOk(self, rv, status_code):
        self.assertEqual(rv.status_code, status_code)
        self.assertEqual(rv.get_json()['output'], 'notok')

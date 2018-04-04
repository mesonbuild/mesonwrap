#!/usr/bin/env python3

import git
import io
import json
import os.path
import shutil
import subprocess
import sys
import tempfile
import time
from tools.repoinit import RepoBuilder
import unittest
import webapi
import zipfile


ROOT = os.path.dirname(sys.argv[0])
SERVER = [sys.executable, os.path.join(ROOT, 'runserver.py')]
WRAPUPDATER = [sys.executable, os.path.join(ROOT, 'mesonwrap.py'), 'wrapupdate']
DBFILE = os.path.join(ROOT, 'wrapdb.sqlite')


class Project:

    def __init__(self, name, version, revision):
        self.name = name
        self.version = version
        self.revision = revision

    def __repr__(self):
        return 'Project("%s", "%s", "%s")' % (self.name, self.version, self.revision)


# revision is not exact match, it should be at least that number, but might be higher
projects = [
    Project(name='protobuf', version='3.5.1', revision=2),
    Project(name='protobuf', version='3.5.0', revision=2),
    Project(name='zlib', version='1.2.8', revision=8),
    Project(name='zlib', version='1.2.11', revision=1),
    Project(name='json', version='2.1.1', revision=1),
]


class Server(subprocess.Popen):

    def __init__(self):
        super(Server, self).__init__(args=SERVER)
        self.api = webapi.WebAPI('http://localhost:5000')
        self._wait_server_ready()

    def _wait_server_ready(self):
        while not self.api.ping():
            time.sleep(0.1)


class FakeProject:

    def __init__(self, name, tmpdir):
        self.name = name
        self.builder = RepoBuilder(name, os.path.join(tmpdir, name))

    def create_version(self, version, base='master', message='Add files'):
        self.builder.create_version(
            version=version,
            zipurl='http://localhost/file.zip',
            filename='file.zip',
            directory='project',
            ziphash='myhash',
            base=base)
        with self.builder.open('meson.build', 'w') as ofile:
            ofile.write("project('hello world')\n")
        self.builder.repo.index.commit(message)

    def commit(self, message):
        return self.builder.repo.index.commit(message)

    def merge_commit(self, message, parent):
        return self.builder.repo.index.commit(
            message, parent_commits=(self.builder.repo.head.commit, parent))

    @property
    def url(self):
        return self.builder.repo.git_dir

    @property
    def repo(self):
        return self.builder.repo


class IntegrationTestBase(unittest.TestCase):

    def setUp(self):
        try:
            os.unlink(DBFILE)
        except FileNotFoundError:
            pass
        self.server = Server()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        self.server.terminate()
        self.server.wait()
        shutil.rmtree(self.tmpdir)

    def assertLooseUploaded(self, project):
        projects = self.server.api.projects()
        self.assertIn(project.name, projects)
        self.assertIn(project.version, projects[project.name].versions)
        self.assertLessEqual(project.revision, projects[project.name].versions[project.version].latest.revision)

    def assertUploaded(self, project):
        projects = self.server.api.projects()
        self.assertIn(project.name, projects)
        self.assertIn(project.version, projects[project.name].versions)
        self.assertIn(project.revision, projects[project.name].versions[project.version].revisions)

    def wrapupdater(self, name, url, version):
        subprocess.check_call(args=WRAPUPDATER + [name, url, version])


class ConsistentVersioningTest(IntegrationTestBase):

    def testRevisions(self):
        prod = webapi.WebAPI('https://wrapdb.mesonbuild.com')
        projects = prod.projects()
        for project in projects:
            for ver_id, version in project.versions.items():
                self.wrapupdater(project.name, 'https://github.com/mesonbuild/{}.git'.format(project.name), ver_id)
                self.assertUploaded(Project(project.name, ver_id, version.latest.revision))
                rev = self.server.api.projects()[project.name].versions[ver_id].latest
                self.assertEqual(version.latest.revision, rev.revision)
                self.assertIn(b'[wrap-file]', rev.wrap)
                self.assertIn(b'directory', rev.wrap)
                self.assertIn(b'source_url', rev.wrap)
                self.assertIn(b'source_filename', rev.wrap)
                self.assertIn(b'source_hash', rev.wrap)
                self.assertIn(b'patch_url', rev.wrap)
                self.assertIn(b'patch_filename', rev.wrap)
                self.assertIn(b'patch_hash', rev.wrap)
                with zipfile.ZipFile(io.BytesIO(rev.zip)) as zipf:
                    self.assertGreater(len(zipf.namelist()), 0)


class WrapUpdaterTest(IntegrationTestBase):

    def test_existing_wrapupdater(self):
        for project in projects:
            url = 'https://github.com/mesonbuild/{name}.git'.format(name=project.name)
            self.wrapupdater(project.name, url, project.version)
            self.assertIn(project.name, self.server.api.projects())
            self.assertLooseUploaded(project)

    def test_wrapupdater(self):
        f = FakeProject('test1', self.tmpdir)
        f.create_version('1.0.0')
        f.create_version('1.0.1')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.1')
        self.assertIn(f.name, self.server.api.projects())
        self.assertUploaded(Project(f.name, '1.0.0', 1))
        self.assertUploaded(Project(f.name, '1.0.1', 1))

    def test_wrapupdater_revisions(self):
        f = FakeProject('test2', self.tmpdir)
        f.create_version('1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.0')
        f.commit('update')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 1))
        self.assertUploaded(Project(f.name, '1.0.0', 2))

    def test_wrapupdater_branched_revisions(self):
        f = FakeProject('test3', self.tmpdir)
        f.create_version('1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.0')
        f.create_version('1.0.1', base='1.0.0', message='New [wrap version]')
        self.wrapupdater(f.name, f.url, '1.0.1')
        f.commit('another commit')
        self.wrapupdater(f.name, f.url, '1.0.1')
        self.assertUploaded(Project(f.name, '1.0.0', 1))
        self.assertUploaded(Project(f.name, '1.0.1', 1))
        self.assertUploaded(Project(f.name, '1.0.1', 2))

    def test_wrapupdater_merged_revisions(self):
        f = FakeProject('test', self.tmpdir)
        f.create_version('1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 1))
        f.commit('commit 1')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 2))
        p = f.commit('commit 2')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 3))
        f.commit('commit 3')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 4))
        f.merge_commit('commit 4', parent=p)
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 5))
        f.merge_commit('commit 5', parent=p)
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 6))

    def test_wrapupdater_latest_revision_only(self):
        f = FakeProject('test3', self.tmpdir)
        f.create_version('1.0.0')
        f.commit('revision 2')
        f.create_version('1.0.1', base='1.0.0', message='New [wrap version]')
        f.commit('revision 2')
        f.commit('revision 3')
        f.commit('revision 4')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.1')
        self.assertUploaded(Project(f.name, '1.0.0', 2))
        self.assertUploaded(Project(f.name, '1.0.1', 4))


if __name__ == '__main__':
    unittest.main()

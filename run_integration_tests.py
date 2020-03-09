#!/usr/bin/env python3

import random
import os
import os.path
import subprocess
import sys
import tempfile
import time
import unittest

from mesonwrap import webapi
from mesonwrap.tools.repoinit import RepoBuilder


ROOT = os.path.dirname(sys.argv[0])
SERVER = [sys.executable, os.path.join(ROOT, 'mesonwrap.py'), 'serve']
WRAPUPDATER = [sys.executable, os.path.join(ROOT, 'mesonwrap.py'),
               'wrapupdate']
PORT = random.randint(10000, 49151)


class Project:

    def __init__(self, name, version, revision):
        self.name = name
        self.version = version
        self.revision = revision

    def __repr__(self):
        return ('Project("%s", "%s", "%s")' %
                (self.name, self.version, self.revision))


class Server(subprocess.Popen):

    def __init__(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        super().__init__(args=SERVER + [
            '--db-directory=' + self._tmpdir.name,
            '--port={}'.format(PORT),
        ])
        self.api = webapi.WebAPI('http://localhost:{}'.format(PORT))
        self._wait_server_ready()

    def _wait_server_ready(self):
        while not self.api.ping():
            time.sleep(0.1)

    @property
    def dbdir(self):
        return self._tmpdir.name

    def close(self):
        self.terminate()
        self.wait()
        self._tmpdir.cleanup()


class FakeProject:

    def __init__(self, name, tmpdir):
        self.name = name
        self.builder = RepoBuilder(name, os.path.join(tmpdir, name))

    def close(self):
        self.builder.close()

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
        self.server = Server()
        self.fake_projects = []
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.server.close()
        for fake_project in self.fake_projects:
            fake_project.close()
        self.tmpdir.cleanup()

    def fake_project(self, name) -> FakeProject:
        """Automatically closes FakeProject on test tearDown."""
        fake_project = FakeProject(name, self.tmpdir.name)
        self.fake_projects.append(fake_project)
        return fake_project

    def assertLooseUploaded(self, project):
        projects = self.server.api.projects()
        self.assertIn(project.name, projects)
        self.assertIn(project.version, projects[project.name].versions)
        self.assertLessEqual(
            project.revision,
            projects[project.name].versions[project.version].latest.revision)

    def assertUploaded(self, project: Project):
        projects = self.server.api.projects()
        self.assertIn(project.name, projects)
        self.assertIn(project.version, projects[project.name].versions)
        self.assertIn(
            project.revision,
            projects[project.name].versions[project.version].revisions)

    def assertLatest(self, project, version, revision):
        latest = self.server.api.projects()[project].query_latest()
        self.assertEqual(latest.version.version, version)
        self.assertEqual(latest.revision, revision)

    def wrapupdater(self, name, url, version):
        subprocess.check_call(args=WRAPUPDATER + [
            '--dbdir=' + self.server.dbdir,
            name, url, version])


class QueryTest(IntegrationTestBase):

    def test_latest(self):
        f = self.fake_project('test1')
        for version in ['1.0.0', '0.1.2', '1.2.1']:
            f.create_version(version)
            self.wrapupdater(f.name, f.url, version)
        self.assertLatest('test1', '1.2.1', 1)
        f.create_version('1.3.0')
        self.wrapupdater(f.name, f.url, '1.3.0')
        self.assertLatest('test1', '1.3.0', 1)
        f.commit('update')
        f.commit('update')
        self.wrapupdater(f.name, f.url, '1.3.0')
        self.assertLatest('test1', '1.3.0', 3)

    def test_latest_semantic_version_comparison(self):
        """Lexicographical comparison leads to the opposite results."""
        f = self.fake_project('test')
        for version in ['1.2.8', '1.2.11']:
            f.create_version(version)
            self.wrapupdater(f.name, f.url, version)
        self.assertLatest('test', '1.2.11', 1)

    def test_latest_non_semantic_version_no_minor(self):
        """Not every project supports semantic versioning, test fallback."""
        f = self.fake_project('test')
        for version in ['1.2', '1.3', '1.7']:
            f.create_version(version)
            self.wrapupdater(f.name, f.url, version)
        self.assertLatest(f.name, '1.7', 1)

    def test_latest_non_semantic_version_single_number(self):
        """If it is not a semantic version just sort lexicographically."""
        f = self.fake_project('test')
        for version in ['212345', '123456']:
            f.create_version(version)
            self.wrapupdater(f.name, f.url, version)
        self.assertLatest(f.name, '212345', 1)

    def test_latest_non_semantic_version_letters(self):
        f = self.fake_project('test')
        for version in ['17a', '2b']:
            f.create_version(version)
            self.wrapupdater(f.name, f.url, version)
        self.assertLatest(f.name, '17a', 1)

    def test_latest_does_not_exist(self):
        with self.assertRaisesRegex(webapi.APIError, 'No such project'):
            self.server.api._api.query_v1_get_latest('non-existent-project')

    def test_by_name_prefix(self):
        baz = self.fake_project('baz')
        baz.create_version('1.0.0')
        self.wrapupdater(baz.name, baz.url, '1.0.0')
        bar = self.fake_project('bar')
        bar.create_version('2.1.1')
        self.wrapupdater(bar.name, bar.url, '2.1.1')
        projects = self.server.api.projects()
        self.assertCountEqual(projects.query_by_name_prefix('baz'),
                              [projects['baz']])
        self.assertCountEqual(projects.query_by_name_prefix('bar'),
                              [projects['bar']])
        self.assertCountEqual(projects.query_by_name_prefix('ba'),
                              [projects['baz'], projects['bar']])


class GithubHookTest(IntegrationTestBase):

    def test_import(self):
        foo = self.fake_project('foobar')
        foo.create_version('1.2.3')
        self.server.api.pull_request_hook('mesonbuild', 'foobar', '1.2.3',
                                          foo.url)
        self.assertUploaded(Project(foo.name, '1.2.3', 1))

    def test_restricted_project(self):
        foo = self.fake_project('meson')
        foo.create_version('1.2.3')
        with self.assertRaisesRegex(webapi.APIError,
                                    'Not a mesonwrap project'):
            self.server.api.pull_request_hook('mesonbuild', 'meson', '1.2.3',
                                              foo.url)


class WrapUpdaterTest(IntegrationTestBase):

    def test_existing_wrapupdater(self):
        location = 'https://github.com/mesonbuild/{}.git'
        # revision is not exact match, it should be at least that number,
        # but might be higher
        projects = [
            Project(name='protobuf', version='3.5.1', revision=2),
            Project(name='protobuf', version='3.5.0', revision=2),
            Project(name='zlib', version='1.2.8', revision=8),
            Project(name='zlib', version='1.2.11', revision=1),
            Project(name='json', version='2.1.1', revision=1),
        ]
        for project in projects:
            with self.subTest(project=project.name):
                url = location.format(project.name)
                self.wrapupdater(project.name, url, project.version)
                self.assertIn(project.name, self.server.api.projects())
                self.assertLooseUploaded(project)

    def test_wrapupdater(self):
        f = self.fake_project('test1')
        f.create_version('1.0.0')
        f.create_version('1.0.1')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.1')
        self.assertIn(f.name, self.server.api.projects())
        self.assertUploaded(Project(f.name, '1.0.0', 1))
        self.assertUploaded(Project(f.name, '1.0.1', 1))

    def test_wrapupdater_revisions(self):
        f = self.fake_project('test2')
        f.create_version('1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.0')
        f.commit('update')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 1))
        self.assertUploaded(Project(f.name, '1.0.0', 2))

    def test_wrapupdater_branched_revisions(self):
        f = self.fake_project('test3')
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
        f = self.fake_project('test')
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
        f = self.fake_project('test3')
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

    def test_bad_upstream_wrap(self):
        f = self.fake_project('test')
        f.create_version('1.0.0')
        with f.builder.open('upstream.wrap', 'w') as up:
            up.write('[wrap-file]\nhello = world\n')
        f.commit('revision 2')
        with self.assertRaises(subprocess.CalledProcessError):
            self.wrapupdater(f.name, f.url, '1.0.0')


if __name__ == '__main__':
    unittest.main()

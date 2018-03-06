#!/usr/bin/env python3

import git
import json
import os.path
import shutil
import subprocess
import sys
import tempfile
import time
from tools.repoinit import RepoBuilder
import unittest
import urllib.error
import urllib.request


ROOT = os.path.dirname(sys.argv[0])
SERVER = [sys.executable, os.path.join(ROOT, 'runserver.py')]
WRAPUPDATER = [sys.executable, os.path.join(ROOT, 'wrapupdater.py')]
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
    Project(name='protobuf', version='3.5.0', revision=2),
    Project(name='zlib', version='1.2.8', revision=8),
    Project(name='zlib', version='1.2.11', revision=1),
    Project(name='json', version='2.1.1', revision=1),
]


class Server(subprocess.Popen):

    def __init__(self):
        super(Server, self).__init__(args=SERVER)
        self._wait_server_ready()

    def _wait_server_ready(self):
        while True:
            try:
                self.fetch('/')
                break
            except urllib.error.URLError:
                time.sleep(0.1)

    def fetch(self, addr):
        with urllib.request.urlopen('http://localhost:5000' + addr) as r:
            return r.read()

    def fetch_json(self, addr):
        j = json.loads(self.fetch(addr).decode('utf8'))
        if j['output'] != 'ok':
            raise ValueError('Bad server response')
        return j

    def projects(self):
        return self.fetch_json('/v1/projects')['projects']

    def project(self, name):
        return self.fetch_json('/v1/projects/' + name)


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
        self.builder.repo.index.commit(message)

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
        for v in self.server.project(project.name)['versions']:
            if v['branch'] == project.version and v['revision'] >= project.revision:
                return
        self.fail('{!r} not found'.format(project))

    def assertUploaded(self, project):
        for v in self.server.project(project.name)['versions']:
            if v['branch'] == project.version and v['revision'] == project.revision:
                return
        self.fail('{!r} not found'.format(project))


class WrapUpdaterTest(IntegrationTestBase):

    def wrapupdater(self, name, url, version):
        subprocess.check_call(args=WRAPUPDATER + [name, url, version])

    def test_existing_wrapupdater(self):
        for project in projects:
            url = 'https://github.com/mesonbuild/{name}.git'.format(name=project.name)
            self.wrapupdater(project.name, url, project.version)
            self.assertIn(project.name, self.server.projects())
            self.assertLooseUploaded(project)

    def test_wrapupdater(self):
        f = FakeProject('test1', self.tmpdir)
        f.create_version('1.0.0')
        f.create_version('1.0.1')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.wrapupdater(f.name, f.url, '1.0.1')
        self.assertIn(f.name, self.server.projects())
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
        f.repo.index.commit('commit 1')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 2))
        p = f.repo.index.commit('commit 2')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 3))
        f.repo.index.commit('commit 3')
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 4))
        f.repo.index.commit('commit 4', parent_commits=(p, f.repo.head.commit))
        self.wrapupdater(f.name, f.url, '1.0.0')
        self.assertUploaded(Project(f.name, '1.0.0', 5))
        f.repo.index.commit('commit 5', parent_commits=(p, f.repo.head.commit))
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

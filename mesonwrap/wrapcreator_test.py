import git
import hashlib
import io
import os
import os.path
import unittest
import zipfile

from mesonwrap import gitutils
from mesonwrap import tempfile
from mesonwrap import upstream
from mesonwrap import wrapcreator


class WrapCreatorTest(unittest.TestCase):

    def setUp(self):
        self._workdir = tempfile.TemporaryDirectory()
        self.workdir = self._workdir.name

    def tearDown(self):
        self._workdir.cleanup()

    def mkfile(self, filename, contents=b''):
        with open(os.path.join(self.workdir, filename), 'wb') as f:
            f.write(contents)

    def mkdir(self, dirname):
        os.makedirs(os.path.join(self.workdir, dirname))

    def test_make_zip(self):
        self.mkfile('.gitignore')
        self.mkfile('upstream.wrap', b'hello world')
        self.mkdir('.git')
        self.mkfile('.git/hello')
        self.mkfile('meson.wrap', b'meson project')
        self.mkdir('hello')
        self.mkfile('hello/world', b'some contents')
        with io.BytesIO() as zipf:
            wrapcreator._make_zip(zipf, self.workdir, 'myprefix')
            with zipfile.ZipFile(zipf, 'r') as zip:
                self.assertListEqual(zip.namelist(), [
                    'myprefix/meson.wrap',
                    'myprefix/hello/world',
                ])
                self.assertEqual(zip.read('myprefix/meson.wrap'),
                                 b'meson project')
                self.assertEqual(zip.read('myprefix/hello/world'),
                                 b'some contents')

    def test_check_definition_empty(self):
        with self.assertRaises(RuntimeError):
            wrapcreator._check_definition(upstream.UpstreamWrap())

    def test_check_definition_okay(self):
        up = upstream.UpstreamWrap()
        up.directory = 'hello'
        up.source_url = 'https://example.com/file.tgz'
        up.source_filename = 'file.tgz'
        up.source_hash = 'hash-hash-hash'
        try:
            wrapcreator._check_definition(up)
        except RuntimeError as e:
            self.fail('Unexpected RuntimeError {!r}'.format(e))

    def test_make_wrap(self):
        repo = git.Repo.init(self.workdir)
        repo.index.commit('initial commit')
        repo.head.reference = repo.create_head('1.2.3')

        def gopen(path, mode='r'):
            return gitutils.GitFile.open(repo, path, mode)

        with gopen('upstream.wrap', 'w') as f:
            upstream.UpstreamWrap(
                directory='hello',
                source_url='https://example.com/file.tgz',
                source_filename='file.tgz',
                source_hash='hash-hash-hash').write(f)
        with gopen('meson.wrap', 'w') as f:
            f.write('hello world')
        repo.index.commit('my commit')
        wrap = wrapcreator.make_wrap('project', repo.git_dir, '1.2.3')
        up = upstream.UpstreamWrap.from_string(wrap.wrap)
        self.assertEqual(up.directory, 'hello')
        self.assertEqual(up.source_url, 'https://example.com/file.tgz')
        self.assertEqual(up.source_filename, 'file.tgz')
        self.assertEqual(up.source_hash, 'hash-hash-hash')
        self.assertEqual(up.patch_url, 'https://wrapdb.mesonbuild.com/v1/'
                                       'projects/project/1.2.3/1/get_zip')
        self.assertEqual(up.patch_filename, 'project-1.2.3-1-wrap.zip')
        with io.BytesIO(wrap.zip) as zipf:
            with zipfile.ZipFile(zipf, 'r') as zip:
                self.assertListEqual(zip.namelist(), ['hello/meson.wrap'])
                self.assertEqual(zip.read('hello/meson.wrap'), b'hello world')
        self.assertEqual(up.patch_hash, hashlib.sha256(wrap.zip).hexdigest())
        self.assertEqual(wrap.wrap_name, 'project-1.2.3-1-wrap.wrap')
        self.assertEqual(wrap.zip_name, 'project-1.2.3-1-wrap.zip')


if __name__ == '__main__':
    unittest.main()

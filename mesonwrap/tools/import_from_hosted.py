import argparse
import os.path

import git
import github
from retrying import retry

from mesonwrap import gitutils
from mesonwrap import tempfile
from mesonwrap import webapi
from mesonwrap import wrap
from mesonwrap.tools import environment


class Importer:

    def __init__(self):
        self._tmp = None
        self._projects = None

    @property
    def _org(self):
        return environment.Github().get_organization('mesonbuild')

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._projects = dict()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._tmp.__exit__(exc_type, exc_value, traceback)
        self._tmp = None
        self._projects = None

    def _clone(self, project):
        if project not in self._projects:
            repo = self._org.get_repo(project)
            path = os.path.join(self._tmp.name, project)
            self._projects[project] = git.Repo.clone_from(repo.clone_url,
                                                          to_path=path)
        return self._projects[project]

    def import_project(self, project):
        for version in project.versions.values():
            self.import_version(version)

    def import_version(self, version):
        for revision in version.revisions.values():
            self.import_revision(revision)

    @staticmethod
    def _get_commit(repo, branch, revision):
        cur = repo.refs['origin/' + branch].commit
        todo = [cur]
        while todo:
            cur = todo.pop()
            rev = gitutils.get_revision(repo, cur)
            if rev > revision:
                todo.extend(cur.parents)
            elif rev == revision:
                return cur
            else:
                raise ValueError('Impossible revision')

    @staticmethod
    def _is_github_error(exception):
        return isinstance(exception, github.GithubException)

    @retry(stop_max_attempt_number=3,
           retry_on_exception=_is_github_error)
    def import_wrap(self, wrap: wrap.Wrap):
        wrappath = os.path.join(self._tmp.name, wrap.name + '.wrap')
        zippath = os.path.join(self._tmp.name, wrap.name + '.zip')
        repo = self._clone(wrap.name)
        with open(wrappath, 'wb') as f:
            f.write(wrap.wrap)
        with open(zippath, 'wb') as f:
            f.write(wrap.zip)
        commit = self._get_commit(repo, wrap.version, wrap.revision)
        ghrepo = self._org.get_repo(wrap.name)
        tagname = '{}-{}'.format(wrap.version, wrap.revision)
        try:
            rel = ghrepo.get_release(tagname)
            print('Release found')
        except github.GithubException:
            tag = ghrepo.create_git_tag(tag=tagname, message=tagname,
                                        type='commit', object=commit.hexsha)
            ghrepo.create_git_ref('refs/tags/{}'.format(tag.tag), tag.sha)
            rel = ghrepo.create_git_release(tag=tagname, name=tagname,
                                            message=tagname)
            print('Release created')
        patch_label = 'patch.zip'
        wrap_label = 'upstream.wrap'
        patch_found = False
        wrap_found = False
        for a in rel.get_assets():
            if a.label == patch_label:
                patch_found = True
            elif a.label == wrap_label:
                wrap_found = True
            else:
                print('Removing unknown asset {!r} / {!r}'.format(a.label,
                                                                  a.name))
                a.delete_asset()
        if not wrap_found:
            rel.upload_asset(wrappath, label=wrap_label,
                             content_type='text/plain')
        if not patch_found:
            rel.upload_asset(zippath, label=patch_label,
                             content_type='application/zip')

    def import_revision(self, revision):
        wrap = revision.combined_wrap
        print(wrap.name,
              wrap.version,
              wrap.revision)
        self.import_wrap(wrap)
        print('Done')


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('--wrapdb_url', default='http://wrapdb.mesonbuild.com')
    parser.add_argument('--project')
    parser.add_argument('--version', help='Does not work without --project')
    parser.add_argument('--revision', help='Does not work without --version')
    args = parser.parse_args(args)
    api = webapi.WebAPI(args.wrapdb_url)
    projects = api.projects()
    with Importer() as imp:
        if args.project:
            project = projects[args.project]
            if args.version:
                version = project.versions[args.version]
                if args.revision:
                    imp.import_revision(version.revisions[args.revision])
                else:
                    imp.import_version(version)
            else:
                imp.import_project(project)
        else:
            for project in projects:
                imp.import_project(project)

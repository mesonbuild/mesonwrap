import argparse
import os.path

import github
from retrying import retry

from mesonwrap import tempfile
from mesonwrap import wrap
from mesonwrap import wrapcreator
from mesonwrap.tools import environment


def _is_github_error(exception):
    return isinstance(exception, github.GithubException)


class Publisher:

    @staticmethod
    def _get_project(
        organization: str, project: str
    ) -> github.Repository.Repository:
        gh = environment.github()
        org = gh.get_organization('mesonbuild')
        return org.get_repo(project)

    @classmethod
    @retry(stop_max_attempt_number=3,
           retry_on_exception=_is_github_error)
    def _import_wrap(cls, tmp, organization: str, wrap: wrap.Wrap) -> None:
        wrappath = os.path.join(tmp, wrap.name + '.wrap')
        zippath = os.path.join(tmp, wrap.name + '.zip')
        with open(wrappath, 'w') as f:
            f.write(wrap.wrap)
        with open(zippath, 'wb') as f:
            f.write(wrap.zip)
        ghrepo = cls._get_project(organization, wrap.name)
        tagname = '{}-{}'.format(wrap.version, wrap.revision)
        try:
            rel = ghrepo.get_release(tagname)
            print('Release {!r} already exists'.format(tagname))
        except github.GithubException:
            tag = ghrepo.create_git_tag(tag=tagname, message=tagname,
                                        type='commit', object=wrap.commit_sha)
            ghrepo.create_git_ref('refs/tags/{}'.format(tag.tag), tag.sha)
            rel = ghrepo.create_git_release(tag=tagname, name=tagname,
                                            message=tagname)
            print('Release {!r} created'.format(tagname))
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
                print('Removing unknown asset {!r} / {!r}'.format(
                        a.label, a.name))
                a.delete_asset()
        if not wrap_found:
            rel.upload_asset(wrappath, label=wrap_label,
                             content_type='text/plain')
        if not patch_found:
            rel.upload_asset(zippath, label=patch_label,
                             content_type='application/zip')

    @classmethod
    def publish(cls, organization: str, project: str, branch: str):
        ghrepo = cls._get_project(organization, project)
        wrap = wrapcreator.make_wrap(project, ghrepo.clone_url, branch)
        with tempfile.TemporaryDirectory() as tmp:
            cls._import_wrap(tmp, organization, wrap)


def publish(organization: str, project: str, branch: str):
    Publisher.publish(organization, project, branch)


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('name')
    parser.add_argument('branch')
    parser.add_argument('--test',
                        action='store_const', const='mesonbuild-test',
                        dest='organization', default='mesonbuild',
                        help='Use mesonbuild-test organization')
    args = parser.parse_args(args)
    publish(args.organization, args.name, args.branch)

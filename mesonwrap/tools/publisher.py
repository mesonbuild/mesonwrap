import argparse
import os.path

import github
import hashlib
import requests
from retrying import retry

from mesonwrap import ini
from mesonwrap import tempfile
from mesonwrap import wrap
from mesonwrap import wrapcreator
from mesonwrap.tools import environment


def _is_github_error(exception):
    return isinstance(exception, github.GithubException)


class Publisher:

    @classmethod
    @retry(stop_max_attempt_number=3,
           retry_on_exception=_is_github_error)
    def _import_wrap(cls, tmp, organization: str, wrap: wrap.Wrap) -> None:
        wrappath = os.path.join(tmp, wrap.name + '.wrap')
        zippath = os.path.join(tmp, wrap.name + '.zip')
        with open(wrappath, 'w') as f:
            f.write(wrap.wrapfile_content)
        with open(zippath, 'wb') as f:
            f.write(wrap.zip)
        ghrepo = environment.repo(organization, wrap.name)
        tagname = f'{wrap.version}-{wrap.revision}'
        try:
            rel = ghrepo.get_release(tagname)
            print(f'Release {tagname!r} already exists')
        except github.GithubException:
            tag = ghrepo.create_git_tag(tag=tagname, message=tagname,
                                        type='commit', object=wrap.commit_sha)
            ghrepo.create_git_ref(f'refs/tags/{tag.tag}', tag.sha)
            rel = ghrepo.create_git_release(tag=tagname, name=tagname,
                                            message=tagname)
            print(f'Release {tagname!r} created')
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
                print(f'Removing unknown asset {a.label!r} / {a.name!r}')
                a.delete_asset()
        if not patch_found:
            # Reupload all assets since wrapfile remembers the hash of zipfile.
            for a in rel.get_assets():
                if a.label == wrap_label:
                    print(f'Deleting {a.label!r}')
                    a.delete_asset()
            print(f'Uploading {wrap_label!r}')
            rel.upload_asset(wrappath, label=wrap_label,
                             content_type='text/plain')
            print(f'Uploading {patch_label!r}')
            rel.upload_asset(zippath, label=patch_label,
                             content_type='application/zip')
        elif not wrap_found:
            # TODO: handle this in wrapcreator
            assert patch_found
            wrapfile = ini.WrapFile.from_string(wrap.wrapfile_content)
            for a in rel.get_assets():
                if a.label == patch_label:
                    with requests.get(a.browser_download_url) as rv:
                        rv.raise_for_status()
                        sha256 = hashlib.sha256(rv.content).hexdigest()
                        wrapfile.patch_hash = sha256
            wrapfile.write_file(wrappath)
            print(f'Uploading {wrap_label!r}')
            rel.upload_asset(wrappath, label=wrap_label,
                             content_type='text/plain')

    @classmethod
    def publish(cls, organization: str, project: str, branch: str):
        ghrepo = environment.repo(organization, project)
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

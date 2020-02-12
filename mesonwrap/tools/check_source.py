import argparse
import concurrent.futures
import hashlib
import http
import io
from typing import Tuple
import urllib.request

from mesonwrap import requests
from mesonwrap import upstream
from mesonwrap import webapi
from mesonwrap import wrap

PYTHON_USERAGENT = urllib.request.URLopener.version

HTTPStatus = Tuple[http.HTTPStatus, str]


def check_source(
    wrapfile: upstream.WrapFile,
    useragent=None,
    timeout=None
) -> HTTPStatus:
    headers = {}
    if useragent:
        headers['User-Agent'] = useragent
    try:
        h = hashlib.sha256()
        with requests.get(wrapfile.source_url, timeout=timeout) as rv:
            h.update(rv.content)
        calculated_hash = h.hexdigest()
        if calculated_hash != wrapfile.source_hash:
            return 0, 'Bad source file hash'
        return rv.status_code, rv.reason
    except OSError as e:
        return 0, str(e)


def check_project(project, useragent, timeout) -> str:
    with io.StringIO() as result:
        try:
            for version in project.versions.values():
                for revision in version.revisions.values():
                    wrapfile = revision.wrapfile
                    print(project.name, version.version, revision.revision,
                          check_source(wrapfile, useragent, timeout),
                          file=result)
        except webapi.APIError:
            print(project.name, 'EMPTY', file=result)
        return result.getvalue()


def check_project_async(wrapdb, project_name, useragent, timeout) -> str:
    project = webapi.WebAPI(wrapdb).projects().query_by_name(project_name)
    assert project
    return check_project(project, useragent, timeout)


def check_all(wrapdb, project_name=None, useragent=None, timeout=None):
    api = webapi.WebAPI(wrapdb)
    projects = api.projects()
    if project_name:
        project = projects.query_by_name(project_name)
        assert project
        print(check_project(project, useragent, timeout))
    else:
        with concurrent.futures.ThreadPoolExecutor() as exe:

            def callback(project):
                return check_project_async(
                    wrapdb, project.name, useragent, timeout)
            for result in exe.map(callback, projects):
                print(result, end='')


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('--wrapdb-url', default='http://wrapdb.mesonbuild.com')
    parser.add_argument('--useragent', default=PYTHON_USERAGENT)
    parser.add_argument('--timeout', type=int, default=60)
    parser.add_argument('--project', default=None)
    args = parser.parse_args(args)
    check_all(wrapdb=args.wrapdb_url, project_name=args.project,
              useragent=args.useragent, timeout=args.timeout)

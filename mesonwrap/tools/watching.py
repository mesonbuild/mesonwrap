import argparse

from mesonwrap.tools import environment
from mesonwrap.tools import repoinit


def get_repositories(gh, organization='mesonbuild'):
    org = gh.get_organization(organization)
    team = org.get_team(repoinit.maintainers_team_id[organization])
    return team.get_repos()


def preamble(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('--test', action='store_true',
                        help='Use http://github.com/mesonbuild-test')
    args = parser.parse_args(args)
    return 'mesonbuild-test' if args.test else 'mesonbuild'


def watch(prog, args):
    organization = preamble(prog, args)
    gh = environment.Github()
    user = gh.get_user()
    for repo in get_repositories(gh, organization):
        user.add_to_watched(repo)


def unwatch(prog, args):
    organization = preamble(prog, args)
    gh = environment.Github()
    user = gh.get_user()
    for repo in get_repositories(gh, organization):
        user.remove_from_watched(repo)

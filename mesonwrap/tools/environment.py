import configparser
import os
import os.path

import github as _github


class Config:

    def __init__(self):
        configpath = os.path.join(
            os.getenv('HOME'), '.config', 'mesonwrap.ini')
        self._config = configparser.ConfigParser()
        self._config.read(configpath)

    @property
    def github_token(self):
        return self._config.get('mesonwrap', 'github_token', fallback=None)


def github():
    return _github.Github(Config().github_token)


def repo(
    organization: str, project: str
) -> _github.Repository.Repository:
    gh = github()
    org = gh.get_organization(organization)
    return org.get_repo(project)

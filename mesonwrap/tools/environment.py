import configparser
import github
import os
import os.path


class Config:

    def __init__(self):
        configpath = os.path.join(os.getenv('HOME'), '.config', 'wrapweb.ini')
        self._config = configparser.ConfigParser()
        self._config.read(configpath)

    @property
    def github_token(self):
        return self._config.get('wrapweb', 'github_token', fallback=None)


def Github():
    return github.Github(Config().github_token)

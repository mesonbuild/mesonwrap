import configparser
import github
import os
import os.path


class Config:

    def __init__(self):
        self._config = configparser.ConfigParser()
        self._config.read(os.path.join(os.getenv('HOME'), '.config', 'wrapweb.ini'))

    @property
    def github_token(self):
        return self._config.get('wrapweb', 'github_token', fallback=None)


def Github():
    return github.Github(Config().github_token)

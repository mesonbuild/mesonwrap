from os.path import dirname, join, normpath


class Config:

    SECRET_KEY = 'changeme please'
    DB_DIRECTORY = normpath(join(dirname(__file__), ".."))
    MODE = 'standalone'  # cache or standalone
    GITHUB_TOKEN = 'change-me-please'

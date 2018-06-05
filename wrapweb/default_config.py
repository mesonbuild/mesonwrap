from os.path import dirname, join, normpath


class Config:

    SECRET_KEY = 'changeme please'
    DB_DIRECTORY = normpath(join(dirname(__file__), ".."))

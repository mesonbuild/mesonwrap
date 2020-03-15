# pylint: skip-file
import requests
from requests import *  # noqa: F401,F403
import requests_ftp.ftp

requests.Session = requests_ftp.ftp.FTPSession
requests.sessions.Session = requests_ftp.ftp.FTPSession

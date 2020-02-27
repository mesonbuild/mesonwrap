import requests
from requests import *
import requests_ftp.ftp

requests.Session = requests_ftp.ftp.FTPSession
requests.sessions.Session = requests_ftp.ftp.FTPSession

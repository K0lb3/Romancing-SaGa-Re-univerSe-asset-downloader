import re
import requests


class API:
    def __init__(self, host):
        self.session = requests.Session()
        self.host = host
        self.session.headers.update({
            "X-Unity-Version":	"2018.4.20f1",
            "User-Agent":	"Dalvik/2.1.0 (Linux; U; Android 5.1.1; SM-N971N Build/LMY49I)",
            "Connection":	"Keep-Alive",
            "Accept-Encoding":	"gzip"
        })

    def get(self, path, **kwargs):
        return self.session.get(f"{self.host}/{path.lstrip('/')}", **kwargs).content

    def post(self, path, **kwargs):
        return self.session.post(f"{self.host}/{path.lstrip('/')}", **kwargs).content

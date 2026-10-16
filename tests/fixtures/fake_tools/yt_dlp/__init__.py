"""FICTIONAL adapter for subprocess tests; never used by live collection."""
import json
from urllib.request import urlopen
from .utils import DownloadError

class YoutubeDL:
    def __init__(self, options): self.options = options
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def extract_info(self, url, download=False):
        try:
            return json.loads(urlopen(url).read())
        except Exception:
            raise DownloadError("FICTIONAL source failed") from None
    def process_info(self, info):
        path = self.options['outtmpl'].replace('%(ext)s', 'wav')
        with open(path, 'wb') as output:
            output.write(urlopen(info['_fixture_media_url']).read())

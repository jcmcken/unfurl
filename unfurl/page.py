import requests
import logging
import re
from bs4 import BeautifulSoup
import hashlib
import sqlite3
import os

LOG = logging.getLogger(__name__)

def get_page(url):
    LOG.debug('fetching page: %s' % url)
    page = requests.get(url)
    LOG.debug('response headers: %s' % page.headers)
    return page

class Page(object):
    def __init__(self, url, regex=None, autoload=False):
        self.url = self._normalize_url(url)
        self._request = None
        self.regex = regex or '.+'

        if autoload:
            self.load()

    def load(self):
        self._request = get_page(self.url)

    def _normalize_url(self, url):
        return url.rstrip('/')

    @property
    def markup(self):
        return self._request.text

    @property
    def links(self):
        if not self.markup:
            return None

        regex = re.compile(self.regex)

        return [ i['href'] for i in \
            BeautifulSoup(self.markup).findAll('a', href=regex) ] 

    @property
    def snapshot(self, regex='.*'):
        """
        Return a snapshot encapsulating the current state of the links on this
        page, including:
 
            * The list of links
            * A crytographic hash representing the data
        """
        return PageSnapshot(self.url, self.links, self.regex)

class PageSnapshot(object):
    DEFAULT_HASH_FUNCTION = hashlib.sha512
    DEFAULT_HASH_ENCODING = 'hex'

    def __init__(self, url=None, links=[], regex=None, hasher=None,
      encoding=None):
        self.url = url
        self.links = links
        self.regex = regex
        self.hasher = hasher or self.DEFAULT_HASH_FUNCTION
        self.encoding = encoding or self.DEFAULT_HASH_ENCODING
        self.links.sort()

    def __eq__(self, other):
        return other.url == self.url and \
               other.regex == self.regex and \
               other.checksum == self.checksum

    @property
    def blob(self):
        """
        Create a unique representation of the link data
        """
        self.links.sort()
        return '\x00'.join(self.links)

    @classmethod
    def unblob(cls, blob):
        return str(blob).split('\x00')

    @property
    def checksum(self):
        return self.hasher(self.blob).digest().encode(self.encoding)

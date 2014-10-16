import requests
import logging
import re
from bs4 import BeautifulSoup
import hashlib
import sqlite3
import os

LOG = logging.getLogger(__name__)

RE_SOMETHING = re.compile('.+')

def get_page(url):
    LOG.debug('fetching page: %s' % url)
    page = requests.get(url)
    LOG.debug('response headers: %s' % page.headers)
    return page

class Page(object):
    def __init__(self, url):
        self.url = self._normalize_url(url)
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

        return [ i['href'] for i in BeautifulSoup(self.markup).findAll('a', href=RE_SOMETHING) ] 

    @property
    def snapshot(self, regex='.*'):
        """
        Return a snapshot encapsulating the current state of the links on this
        page, including:
 
            * The list of links
            * A crytographic hash representing the data
        """
        return PageSnapshot(self.url, self.links)

class PageSnapshot(object):
    DEFAULT_HASH_FUNCTION = hashlib.sha512

    def __init__(self, url=None, links=[]):
        self.url = url
        self.links = links
        self.links.sort()

    def blob(self):
        """
        Create a unique representation of the link data
        """
        self.links.sort()
        return '\x00'.join(self.links)

    def unblob(self, blob):
        return str(blob).split('\x00')

    def checksum(self, hasher=None, encode='hex'):
        hash_func = hasher or self.DEFAULT_HASH_FUNCTION
        return hash_func(self.blob()).digest().encode(encode)

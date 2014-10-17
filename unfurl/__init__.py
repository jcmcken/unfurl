import logging

logging.basicConfig()
LOG = logging.getLogger(__name__)

from unfurl.config import DEBUG_MODE

if DEBUG_MODE:
    LOG.setLevel(logging.DEBUG)
    LOG.debug('debug mode enabled via environment')

from unfurl.page import Page, PageSnapshot
from unfurl.db import Database, Snapshot
from unfurl.crawler import Crawler

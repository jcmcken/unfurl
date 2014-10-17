import logging
import time
import re
from unfurl import Database

LOG = logging.getLogger(__name__)

class Crawler(object):
    def __init__(self, period=3600, db=None):
        self.period = period
        self.db = db or Database()

        LOG.debug('crawler period: %d' % self.period)
        LOG.debug('crawler db: %s' % self.db.location)

    def crawl(self, page):
        page.load()
        self.db.add_snapshot(page.snapshot)        

    def run(self):
        while True:
            time.sleep(self.period)

import logging
import time
import re
from unfurl import Database, Snapshot

LOG = logging.getLogger(__name__)

class Crawler(object):
    def __init__(self, period=3600, db=None):
        self.period = period
        self.db = db or Database()

        LOG.debug('crawler period: %d' % self.period)
        LOG.debug('crawler db: %s' % self.db.location)

    def crawl_page(self, page):
        LOG.debug('crawling %s' % page.url)
        page.load()
       
        if not Snapshot.exact(page.snapshot): 
            LOG.debug("didn't find snapshot in db, adding new entry")
            self.db.add_snapshot(page.snapshot)        
        else:
            LOG.debug("identical snapshot already exists in database, skipping")

    def crawl(self, pages):
        LOG.debug('starting crawl loop')
        while True:
            for page in pages:
                self.crawl_page(page)
            time.sleep(self.period)

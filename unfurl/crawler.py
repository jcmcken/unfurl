import logging
import time
import re
from unfurl import Database, Snapshot

LOG = logging.getLogger(__name__)

class Crawler(object):
    def __init__(self, period=3600, db=None, count=-1):
        self.period = period
        self.count = count
        self.db = db or Database()

        LOG.debug('crawler period: %d' % self.period)
        LOG.debug('crawler count: %d' % self.count)
        LOG.debug('crawler db: %s' % self.db.location)

    def crawl_page(self, page):
        LOG.debug('crawling %s' % page.url)
        page.load()

        if not page.loaded:
            LOG.error('could not load page, skipping')
            return
       
        if not Snapshot.exact(page.snapshot): 
            LOG.debug("didn't find snapshot in db, adding new entry")
            self.db.add_snapshot(page.snapshot)        
        else:
            LOG.debug("identical snapshot already exists in database, skipping")

    def crawl(self, pages):
        LOG.debug('starting crawl loop')
        elapsed = 0

        if self.count == 0:
            return

        while True:
            start = time.time()
            for page in pages:
                self.crawl_page(page)

            elapsed += 1

            if elapsed == self.count:
                break

            LOG.debug('round %d took %.3f seconds total' % \
                (elapsed, (time.time() - start)))
            
            self.sleep()

    def sleep(self):
        LOG.debug('sleeping for %d seconds' % self.period)
        time.sleep(self.period)

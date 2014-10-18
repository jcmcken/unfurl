import logging
import time
import re
from unfurl import Database, Snapshot
from Queue import Queue
from threading import Thread

LOG = logging.getLogger(__name__)

class Executor(object):
    def __init__(self, callable, threaded=True, max_threads=10):
        LOG.info('max threads: %s' % max_threads)
        LOG.info('threaded mode enabled? %s' % threaded)
        self._callable = callable
        self._queue = Queue(max_threads)
        self.threaded = threaded

    def _worker(self):
        while True:
            item = self._queue.get()
            self._callable(item)
            self._queue.task_done()

    def _work_threaded(self, items):
        for item in items:
            t = Thread(target=self._worker)
            t.daemon = True
            t.start()

        for item in items:
            self._queue.put(item)

        self._queue.join()

    def _work_unthreaded(self, items):
        for item in items:
            self._callable(item)

    def work_on(self, items):
        if self.threaded:
            self._work_threaded(items)
        else:
            self._work_unthreaded(items)

class Crawler(object):
    def __init__(self, period=3600, db=None, count=-1, threaded=True, max_threads=5):
        self.period = period
        self.count = count
        self.db = db or Database()
        self.executor = Executor(self.crawl_page, threaded=threaded, max_threads=max_threads)

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
            self.executor.work_on(pages)

            elapsed += 1

            if elapsed == self.count:
                break

            LOG.debug('round %d took %.3f seconds total' % \
                (elapsed, (time.time() - start)))
            
            self.sleep()

    def sleep(self):
        LOG.debug('sleeping for %d seconds' % self.period)
        time.sleep(self.period)

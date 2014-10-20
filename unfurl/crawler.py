import logging
import time
import re
from unfurl import Database, Snapshot
import Queue
import threading
import signal

LOG = logging.getLogger(__name__)

class Executor(object):
    def __init__(self, callable, threaded=True, max_threads=10):
        LOG.info('max threads: %s' % max_threads)
        LOG.info('threaded mode enabled? %s' % threaded)
        self.threaded = threaded

        self._max_threads = max_threads
        self._callable = callable
        self._queue = Queue.Queue()

        self._worker_threads = []

        self._shutdown = threading.Event()

    def _worker(self):
        while not self._shutdown.is_set():
            try:
                # the queue is fully populated from thread start, so no need
                # to block for work
                item = self._queue.get(timeout=1)
            except Queue.Empty:
                # empty queue == no more work == exit thread
                return
            self._callable(item)
            self._queue.task_done()

    def _work_threaded(self, items):
        for i in range(self._max_threads):
            t = threading.Thread(target=self._worker)
            self._worker_threads.append(t)
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

    def shutdown(self):
        LOG.debug('attempting to shut down worker threads')
        self._shutdown.set()

        while self._living_workers():
            time.sleep(0.5)

    def _living_workers(self):
        return [ t for t in self._worker_threads if t.isAlive() ]

class Crawler(object):
    def __init__(self, period=3600, db=None, count=-1, threaded=True, max_threads=5):
        # this this is likely a long-running process, set a better log level
        self._setup_logging()

        self.period = period
        self.count = count
        self.db = db or Database()
        self.executor = Executor(self.crawl_page, threaded=threaded, max_threads=max_threads)

        LOG.info('crawler period: %d' % self.period)
        LOG.info('crawler count: %d' % self.count)
        LOG.info('crawler db: %s' % self.db.location)

    def _setup_logging(self):
        if LOG.level == logging.NOTSET or LOG.level > logging.INFO:
            LOG.setLevel(logging.INFO)

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
        LOG.info('starting crawl loop over %d pages' % len(pages))
        elapsed = 0

        if self.count == 0:
            return

        while True:
            start = time.time()
            try:
                self.executor.work_on(pages)
            except Exception, e:
                LOG.exception('caught unhandled exception')
                self.executor.shutdown()
    
            elapsed += 1

            if elapsed == self.count:
                break

            LOG.info('round %d took %.3f seconds total' % \
                (elapsed, (time.time() - start)))
            
            self.sleep()

        self.executor.shutdown()

    def sleep(self):
        LOG.info('sleeping for %d seconds' % self.period)
        time.sleep(self.period)

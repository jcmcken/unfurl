import time
import logging

LOG = logging.getLogger(__name__)

def timeit(description='action'):
    def timeit_inner(func):
        def wrapped(*args, **kwargs):
            now = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - now
            LOG.debug('%s took %.3f seconds' % (description, elapsed))
            return result
        return wrapped
    return timeit_inner

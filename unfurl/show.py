import difflib
from unfurl.db import Snapshot, Database, NoSuchRecord

class Differ(object):
    def __init__(self, db=None):
        self.db = db or Database()

    def _unified_diff(self, old, new, **kwargs):
        return difflib.unified_diff(old, new, lineterm='')

    def _get_diffables(self, url, old_offset, new_offset):
        new_snap = Snapshot.last(url, new_offset)
        old_snap = Snapshot.last(url, old_offset)

        if not (new_snap or old_snap):
            raise NoSuchRecord(url)

        if not old_snap:
            old_snap = new_snap

        return old_snap, new_snap

    def diff(self, url, old_offset=1, new_offset=0):
        old_snap, new_snap = self._get_diffables(url, old_offset, new_offset)

        new = new_snap.object()
        new_links = new.links
        to_date = new_snap.created

        if not old_snap:
            old_links = new_links
            from_date = to_date
        else:
            old = old_snap.object()
            old_links = old.links
            from_date = old_snap.created

        items = list(difflib.unified_diff(old_links, new_links, lineterm='',
            fromfiledate=from_date, tofiledate=to_date))  
        return '\n'.join(items) + '\n'

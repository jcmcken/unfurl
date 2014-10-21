from peewee import (
  SqliteDatabase, Model, CharField, IntegerField, DateTimeField,
  BlobField,
)
from unfurl.config import CONFIG
from unfurl.page import PageSnapshot
import datetime
import difflib
import sqlite3

_database = SqliteDatabase(None, threadlocals=True)

class BaseModel(Model):
    class Meta:
        database = _database

class Snapshot(BaseModel):
    url = CharField()
    created = DateTimeField(default=datetime.datetime.now)
    data = BlobField()
    checksum = CharField()
    regex = CharField()

    @classmethod
    def last(cls, url=None, offset=None):
        query = cls.select()

        if url:
            query = query.where(cls.url == url)
        
        query = query.order_by(cls.created.desc())

        if offset:
            query = query.limit(1).offset(offset)

        return query.first()

    def object(self):
        return PageSnapshot(
          url=self.url, 
          regex=self.regex,
          links=PageSnapshot.unblob(self.data),
        )

    @classmethod
    def exact(cls, snapshot):
        return cls.select().where(
          (cls.url == snapshot.url) & 
          (cls.checksum == snapshot.checksum) &
          (cls.regex == snapshot.regex)
        ).first()

    @classmethod
    def last_two(cls, url, old_offset=1, new_offset=0):
        new_snap = Snapshot.last(url, new_offset)
        old_snap = Snapshot.last(url, old_offset)

        if not (new_snap or old_snap):
            raise NoSuchRecord(url)

        if not old_snap:
            old_snap = new_snap

        return old_snap, new_snap

    @classmethod
    def diff(cls, url, old_offset=1, new_offset=0):
        old_snap, new_snap = Snapshot.last_two(
            url, old_offset=old_offset, new_offset=new_offset)

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
            fromfiledate=from_date, tofiledate=to_date, 
            tofile=new.url, fromfile=new.url))  
        return '\n'.join(items) + '\n'

class NoSuchRecord(RuntimeError): pass

class Database(object):
    def __init__(self, db=None):
        self._location = db or CONFIG.get('global', 'database')
        self._cursor = _database
        self.initialize()

    @property
    def location(self):
        return self._cursor.database

    def initialize(self):
        self._cursor.init(self._location)
        try:
            self.create_tables()
        except sqlite3.OperationalError, e:
            if 'already exists' not in e.args[0]:
                raise e

    def create_tables(self):
        for table in [Snapshot]:
            self._cursor.create_table(table)

    @classmethod
    def add_snapshot(cls, snapshot):
        return Snapshot(
          url=snapshot.url,
          data=snapshot.blob,
          checksum=snapshot.checksum,
          regex = snapshot.regex,
        ).save()

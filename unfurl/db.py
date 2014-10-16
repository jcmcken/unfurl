from peewee import (
  SqliteDatabase, Model, CharField, IntegerField, DateTimeField,
  BlobField,
)
from unfurl.config import DATABASE
from unfurl.page import PageSnapshot
import datetime

_database = SqliteDatabase(DATABASE)

class BaseModel(Model):
    class Meta:
        database = _database

class Snapshot(BaseModel):
    url = CharField()
    created = DateTimeField(default=datetime.datetime.now)
    data = BlobField()
    checksum = CharField()

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
        snap = PageSnapshot(url=self.url)
        snap.links = snap.unblob(self.data)
        return snap

class Database(object):
    def __init__(self, db=None):
        self._cursor = db or _database

    @property
    def location(self):
        return self._cursor.database

    def initialize(self):
        try:
            self.create_tables()
        except sqlite3.OperationalError, e:
            if 'already exists' not in e.args[0]:
                raise e

    def create_tables(self):
        for table in [Snapshot]:
            self._cursor.create_table(table)

    def add_snapshot(self, snapshot):
        return Snapshot(
          url=snapshot.url,
          data=snapshot.blob(),
          checksum=snapshot.checksum(),
        ).save()

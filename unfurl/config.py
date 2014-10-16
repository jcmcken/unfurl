import os
import logging

LOG = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = '/etc/unfurl.cfg'
DEFAULT_USER_CONFIG_FILE = os.path.expanduser('~/.unfurl/config')
DEFAULT_ENV_CONFIG_FILE = os.environ.get('UNFURL_CONFIG') or None

CONFIG_PRECEDENCE = [ 
  DEFAULT_ENV_CONFIG_FILE,
  DEFAULT_USER_CONFIG_FILE, 
  DEFAULT_CONFIG_FILE
]

def resolve_config_file(precedence=None):
    if DEFAULT_ENV_CONFIG_FILE:
        result = DEFAULT_ENV_CONFIG_FILE
    elif is_root():
        result = DEFAULT_CONFIG_FILE
    else:
        result = DEFAULT_USER_CONFIG_FILE
    LOG.debug('resolved config file: %s' % result)
    return result

DATABASE_FILENAME = 'db.sqlite3'
DEFAULT_DATABASE_DIR = '/var/db/unfurl'
DEFAULT_USER_DIR = os.path.expanduser('~/.unfurl')
MEMORY_DATABASE = ':memory:' # sqlite in-memory db
DEFAULT_DATABASE = os.path.join(DEFAULT_DATABASE_DIR, DATABASE_FILENAME)
DEFAULT_USER_DATABASE = os.path.join(DEFAULT_USER_DIR, DATABASE_FILENAME)
DEFAULT_ENV_DATABASE = os.environ.get('UNFURL_DATABASE') or None

def is_root():
    return os.getuid() == 0

def resolve_database(precedence=None):
    if DEFAULT_ENV_DATABASE:
        result =  DEFAULT_ENV_DATABASE
    elif is_root():
        result = DEFAULT_DATABASE
    else:
        result = DEFAULT_USER_DATABASE
    LOG.debug('resolved database: %s' % result)
    return result

def create_environment(umask=0022):
    os.umask(umask)

    if is_root():
        os.makedirs(DEFAULT_DATABASE_DIR)
    else:
        os.makedirs(DEFAULT_USER_DIR)

CONFIG_FILE = resolve_config_file()
DATABASE = resolve_database()

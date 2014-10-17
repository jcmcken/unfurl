import os
import logging
import ConfigParser
import errno

LOG = logging.getLogger(__name__)

def fullpath(filename):
    return os.path.realpath(os.path.expanduser(filename))

DEFAULT_CONFIG_FILE = '/etc/unfurl.cfg'
DEFAULT_USER_DIR = fullpath('~/.unfurl')
DEFAULT_USER_CONFIG_FILE = os.path.join(DEFAULT_USER_DIR, 'config')
DEFAULT_ENV_CONFIG_FILE = os.environ.get('UNFURL_CONFIG') or None

CONFIG_PRECEDENCE = [ 
  DEFAULT_ENV_CONFIG_FILE,
  DEFAULT_USER_CONFIG_FILE, 
  DEFAULT_CONFIG_FILE
]

def resolve_config_file(precedence=None):
    for candidate in (precedence or CONFIG_PRECEDENCE):
        if candidate and os.path.isfile(candidate):
            return candidate
    return DEFAULT_CONFIG_FILE

DATABASE_FILENAME = 'db.sqlite3'
DEFAULT_DATABASE_DIR = '/var/db/unfurl'
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
    result = fullpath(result)
    LOG.debug('resolved database: %s' % result)
    db_dir = os.path.dirname(result)
    if not os.path.isdir(db_dir):
        LOG.error('database directory "%s" is missing, creating memory db '
                  'instead' % db_dir)
        result = MEMORY_DATABASE
    return result

def create_environment(umask=0022):
    os.umask(umask)

    if is_root():
        os.makedirs(DEFAULT_DATABASE_DIR)
    else:
        os.makedirs(DEFAULT_USER_DIR)

CONFIG_FILE = resolve_config_file()
DATABASE = resolve_database()

class ConfigurationError(RuntimeError): 
    def __init__(self, exception):
        self.exception = exception

    def __str__(self):
        return "wrapped exception: %s" % repr(self.exception)

class Configuration(object):
    defaults = {
      'global': {
        'database': DATABASE,
      },
      'crawler': {
        'period': 3600,
      },
    }

    def __init__(self, filename):
        self.filename = filename
        self._conf = ConfigParser.RawConfigParser(self.defaults)
        self._set_defaults()
        self.load()

    def load(self):
        self._conf.read(self.filename)
        try:
            self._pre_convert_validate()
            self._convert()
            self._post_convert_validate()
        except Exception, e:
            raise ConfigurationError(e)

    def _set_defaults(self):
        for section, section_data in self.defaults.iteritems():
            try:
                self._conf.add_section(section)
            except ConfigParser.DuplicateSectionError:
                pass
            for key, val in section_data.iteritems():
                self.set(section, key, val)

    def get(self, section, key, default=None):
        try:
            return self._conf.get(section, key)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
            return default

    def set(self, section, key, value):
        self._conf.set(section, key, value)

    def _pre_convert_validate(self):
        """
        Validate the syntactic correctness of configuration options
        """
        pass

    def _post_convert_validate(self):
        """
        Validate the semantic correctness of configuration options
        """
        db = self.get('global', 'database')
        if db != MEMORY_DATABASE:
            db_dir = os.path.dirname(db)
            if not os.path.isdir(db_dir):
                raise OSError(errno.EEXIST, 
                  'database directory "%s" does not exist' % db_dir)

    def convert(self, section, key, callable):
        self.set(section, key, callable(self.get(section, key)))

    def _convert(self):
        """
        Convert raw string configurations into appropriate types
        """
        self.convert('crawler', 'period', int)
        db = self.get('global', 'database')
        if db != MEMORY_DATABASE:
            self.convert('global', 'database', fullpath)

CONFIG = Configuration(CONFIG_FILE)

import os
import logging
import ConfigParser
import errno

LOG = logging.getLogger(__name__)

def fullpath(filename):
    return os.path.realpath(os.path.expanduser(filename))

DEBUG_MODE = os.environ.get('UNFURL_DEBUG', 'false').lower() == 'true'

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
        'log_level': 'INFO',
      },
      'crawler': {
        'count': '-1',
        'period': '3600',
        'max_threads': '5',
        'threaded': 'false',
      },
    }

    def __init__(self, filename=None, autoload=False):
        self.filename = filename
        self._conf = ConfigParser.RawConfigParser(self.defaults)
        self._set_defaults()
        self._loaded = False

        if autoload:
            self.load()

    @property
    def loaded(self):
        return self._loaded

    def load(self):
        if self.filename:
            self._conf.read(self.filename)
        try:
            self._pre_convert_validate()
            self._type_conversion()
            self._post_convert_validate()
        except Exception, e:
            raise ConfigurationError(e)
        self._loaded = True

    def ensure_loaded(self):
        if not self.loaded:
            self.load()

    def _set_defaults(self):
        for section, section_data in self.defaults.iteritems():
            try:
                self._conf.add_section(section)
            except ConfigParser.DuplicateSectionError:
                pass
            for key, val in section_data.iteritems():
                self._set(section, key, val)

    def _get(self, section, key, default=None):
        try:
            return self._conf.get(section, key)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
            return default

    def get(self, section, key, default=None):
        self.ensure_loaded()
        return self._get(section, key, default)

    def _set(self, section, key, value):
        self._conf.set(section, key, value)

    def set(self, section, key, value):
        self.ensure_loaded()
        self._set(section, key, value)

    def _pre_convert_validate(self):
        """
        Validate the syntactic correctness of configuration options
        """
        pass

    def _post_convert_validate(self):
        """
        Validate the semantic correctness of configuration options
        """
        db = self._get('global', 'database')
        if db != MEMORY_DATABASE:
            db_dir = os.path.dirname(db)
            if not os.path.isdir(db_dir):
                raise OSError(errno.EEXIST, 
                  'database directory "%s" does not exist' % db_dir)

    def _convert(self, section, key, callable, getter=None, setter=None):
        getter = getter or self._get
        setter = setter or self._set
        converted = callable(getter(section, key))
        LOG.debug('interpreted %s:%s == %s' % (section, key, converted))
        setter(section, key, converted)

    def convert(self, section, key, callable):
        self._convert(section, key, callable, getter=self.get,
            setter=self.set)

    def _boolean(self, item):
        return item.lower().strip() == 'true'

    def _log_level(self, item):
        level = getattr(logging, item.upper(), 'INFO')

    def _type_conversion(self):
        """
        Convert raw string configurations into appropriate types
        """
        self._convert('crawler', 'period', int)
        self._convert('crawler', 'count', int)
        self._convert('crawler', 'max_threads', int)
        self._convert('crawler', 'threaded', self._boolean)
        db = self._get('global', 'database')
        if db != MEMORY_DATABASE:
            self._convert('global', 'database', fullpath)

    def prefer(self, preference, section, key):
        """
        The 'reverse' of get. Use ``preference`` if it's not ``None``,
        otherwise get item from config file.
        """
        if preference is not None:
            return preference
        return self.get(section, key)

DEFAULT_CONFIG = Configuration(autoload=True)
CONFIG = Configuration(CONFIG_FILE)

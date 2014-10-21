import optparse
import logging
import sys
from unfurl import Crawler, Page
from unfurl.config import CONFIG, ConfigurationError
from unfurl.show import Differ
import sqlite3

LOG = logging.getLogger(__name__)

def error(message):
    sys.stderr.write(' unfurl: error: %s\n' % message)

def abort(message):
    error(message)
    raise SystemExit(1)

def get_cli():
    cli = optparse.OptionParser(prog='unfurl',
      usage='unfurl <subcommand> [arguments] [options]',
      epilog='Valid subcommands: %s' % ', '.join(COMMANDS.keys()))
    cli.add_option('--debug', action='store_true',
      help='enable debug output')
    return cli

def get_crawl_cli():
    cli = optparse.OptionParser(prog='unfurl crawl',
        usage='unfurl crawl <url> [url, url, ...] [options]')
    cli.add_option('-p', '--period', type=int, default=3600,
      help='Time in seconds between crawls. Defaults to 1hr')
    cli.add_option('-t', '--count', type=int, default=-1,
      help='Crawl a specified number of times (defaults to forever)')
    return cli

def get_diff_cli():
    cli = optparse.OptionParser(prog='unfurl diff',
        usage='unfurl diff <url> [url, url, ...] [options]')
    cli.add_option('-o', '--old', type=int, default=1,
      help='Offset of the "old" snapshot (0 is latest, 1 is next oldest, etc.)'
           ' Defaults to 1.')
    cli.add_option('-n', '--new', type=int, default=0,
      help='Offset of the "old" snapshot (0 is latest, 1 is next oldest, etc.)'
           ' Defaults to 0.')
    return cli

def main_main(argv):
    cli = get_cli()
    opts, args = cli.parse_args(['-h'])

def main_diff(argv):
    cli = get_diff_cli()
    opts, args = cli.parse_args(argv)

    if len(args) < 1:
        cli.error('requires at least one URL')

    load_config(cli)

    differ = Differ()

    diff = differ.diff(args[0], old_offset=opts.old, new_offset=opts.new)

    sys.stdout.write(diff)
    

def load_config(cli, config=None):
    config = config or CONFIG
    try:
        config.load()
    except ConfigurationError, e:
        cli.error('problem understanding configuration: ' + e.exception.args[0])        

def main_crawl(argv):
    cli = get_crawl_cli()
    opts, args = cli.parse_args(argv)

    if args:
        LOG.debug('command-line set to crawl pages: %s' % ', '.join(args))

    load_config(cli)

    crawler = Crawler(
      period=CONFIG.get('crawler', 'period'),
      count=CONFIG.get('crawler', 'count'),
      threaded=CONFIG.get('crawler', 'threaded'),
      max_threads=CONFIG.get('crawler', 'max_threads')
    )
    pages = [ Page(i) for i in args ]
    crawler.crawl(pages)

def main_snap(argv):
    pass

def main_show(argv):
    pass

COMMANDS = {
  'diff': main_diff,
  'crawl': main_crawl,
  'snap': main_snap,
  'show': main_show,
}

def main(argv=None):
    argv = argv or sys.argv
    argv.pop(0) # discard runtime

    try:
        command = argv.pop(0)
    except IndexError:
        command = None

    if command and command.startswith('-'):
        command = None

    LOG.debug('subcommand is "%s"' % command)

    driver = COMMANDS.get(command, main_main)
    LOG.debug('mapped to driver "%s"' % driver.__name__)

    try:
        driver(argv)
    except sqlite3.OperationalError, e:
        abort(e.args[0])

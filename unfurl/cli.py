import optparse
import logging

logging.basicConfig()
LOG = logging.getLogger(__name__)

def get_cli():
    cli = optparse.OptionParser()
    cli.add_option('--debug', action='store_true',
      help='enable debug output')
    return cli

def main():
    cli = get_cli()
    opts, args = cli.parse_args()

    if opts.debug:
        LOG.setLevel(logging.DEBUG)
        LOG.info('debug mode enabled')

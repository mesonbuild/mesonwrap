import argparse
import sys

from wrapweb.app import APP
from mesonwrap import wrapcreator
from mesonwrap import wrapupdater
from mesonwrap.tools import repoinit, reviewtool, dbtool


class Command:

    CMD_PREFIX = 'command_'

    def __init__(self, command=None):
        parser = argparse.ArgumentParser(usage=self.usage())
        parser.add_argument('command')
        if command is None:
            command = parser.parse_args(sys.argv[1:2]).command
        if not hasattr(self, self.CMD_PREFIX + command):
            print('Unrecognized command', command)
            parser.print_help()
            sys.exit(1)
        getattr(self, self.CMD_PREFIX + command)()

    def usage(self):
        return '{} command\n'.format(sys.argv[0]) + self.format_commands()

    def format_commands(self):
        maxlen = max(len(cmd) for cmd in self.extract_commands().keys())
        fmt = '  {:' + str(maxlen + 1) + '} {}'
        return '\n'.join(
            fmt.format(cmd, descr)
            for cmd, descr in sorted(self.extract_commands().items(),
                                     key=lambda x: x[0])
        )

    def extract_commands(self):
        return {
            cmd[len(self.CMD_PREFIX):] : getattr(self, cmd).__doc__
            for cmd in dir(self) if cmd.startswith(self.CMD_PREFIX)
        }

    def command_serve(self):
        '''Run server'''
        APP.debug = True
        APP.run(host="0.0.0.0")

    def command_review(self):
        '''Review wrap PR'''
        reviewtool.main(sys.argv[2:])

    def command_new_repo(self):
        '''Create and push new wrap repository'''
        repoinit.new_repo(sys.argv[2:])

    def command_new_version(self):
        '''Create new version and prefill upstream.wrap'''
        repoinit.new_version(sys.argv[2:])

    def command_refresh_repo(self):
        '''Refresh statically created file'''
        repoinit.refresh(sys.argv[2:])

    def command_wrapcreate(self):
        '''Create wrap from remote repository'''
        wrapcreator.main(sys.argv[2:])

    def command_wrapupdate(self):
        '''Create wrap and import it into local database'''
        wrapupdater.main(sys.argv[2:])

    def command_dbtool(self):
        '''This is a simple tool to do queries and inserts from the command line'''
        dbtool.main(sys.argv[2:])

#!/usr/bin/env python3

import argparse
import sys
from tools import repoinit, reviewtool
from wrapweb.app import APP


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
        strings = []
        for cmd, descr in sorted(self.extract_commands().items(), key=lambda x: x[0]):
            strings.append('  {:10} {}'.format(cmd, descr))
        return '\n'.join(strings)

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

    def command_repoinit(self):
        '''Initialize new wrap repository'''
        repoinit.main(sys.argv[2:])


if __name__ == '__main__':
    Command()

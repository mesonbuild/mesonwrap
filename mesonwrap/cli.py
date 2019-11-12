import argparse
import inspect
import sys
import typing

from wrapweb import APP
from mesonwrap import wrapcreator
from mesonwrap import wrapupdater
from mesonwrap.tools import repoinit, reviewtool, dbtool
from mesonwrap.tools import import_from_hosted
from mesonwrap.tools import watching


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
            cmd[len(self.CMD_PREFIX):]: getattr(self, cmd).__doc__
            for cmd in dir(self) if cmd.startswith(self.CMD_PREFIX)
        }

    def args(self) -> typing.Tuple[str, typing.List[str]]:
        """Returns (program name, list of arguments)."""
        func = inspect.stack()[1][3]
        command = func[len(self.CMD_PREFIX):]
        return ('{} {}'.format(sys.argv[0], command),
                sys.argv[2:])

    def command_serve(self):
        """Run server"""
        APP.debug = True
        APP.run(host='0.0.0.0')

    def command_review(self):
        """Review wrap PR"""
        reviewtool.main(*self.args())

    def command_new_repo(self):
        """Create and push new wrap repository"""
        repoinit.new_repo(*self.args())

    def command_new_version(self):
        """Create new version and prefill upstream.wrap"""
        repoinit.new_version(*self.args())

    def command_refresh_repo(self):
        """Refresh statically created file"""
        repoinit.refresh(*self.args())

    def command_wrapcreate(self):
        """Create wrap from remote repository"""
        wrapcreator.main(*self.args())

    def command_wrapupdate(self):
        """Create wrap and import it into local database"""
        wrapupdater.main(*self.args())

    def command_dbtool(self):
        """This is a simple tool to do queries and inserts"""
        dbtool.main(*self.args())

    def command_import_from_hosted(self):
        """Import projects from wrapdb into github"""
        import_from_hosted.main(*self.args())

    def command_watch(self):
        """Watch mesonwrap repositories"""
        watching.watch(*self.args())

    def command_unwatch(self):
        """Unwatch mesonwrap repositories"""
        watching.unwatch(*self.args())

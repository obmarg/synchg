import os
import synchg
from ConfigParser import ConfigParser, Error as ConfigParserError
from plumbum import cli, local
from clint import resources
from .sync import SyncRemote, AbortException, SyncError


class SyncHg(cli.Application):
    PROGNAME = 'SyncHg'
    VERSION = synchg.__version__
    DESCRIPTION = 'Syncs a remote mercurial repository'

    ConfigFileName = 'config.ini'

    def __init__(self, *pargs):
        super(SyncHg, self).__init__(*pargs)
        self.config = ConfigParser()

    def _get_config(self, in_do_config=False):
        '''
        Reads the configuration
        '''
        resources.init('obmarg', 'synchg')
        self.config = ConfigParser()
        contents = resources.user.read(self.ConfigFileName)
        if not contents:
            if not in_do_config:
                print "Could not find config file"
                self.do_config()
        else:
            self.config.readfp(resources.user.open(self.ConfigFileName))

    name = cli.SwitchAttr(
            ['n', '--name'],
            help='The directory name of the repository on the remote. '
                 'Uses the local directory name by default'
            )

    @cli.switch(['-c', '--config'])
    def do_config(self):
        '''
        Runs through the initial configuration
        '''
        print "Running initial configuration"
        self._get_config(True)
        srcdir = default = ''
        if not self.config.has_section('config'):
            self.config.add_section('config')
        try:
            default = self.config.get('config', 'hgroot')
        except ConfigParserError:
            pass
        while not srcdir:
            srcdir = raw_input(
                    "Remote source directory? [{0}] ".format(default)
                    )
        self.config.set('config', 'hgroot', srcdir)
        if not os.path.exists(resources.user.path):
            os.makedirs(resources.user.path)
        self.config.write(resources.user.open(self.ConfigFileName, 'w'))
        pass

    def main(self, remote_host, local_path=None):
        self._get_config()
        if local_path:
            local_path = local.cwd / local_path
        else:
            local_path = local.cwd

        if not self.name:
            self.name = local_path.basename

        SyncRemote(remote_host, self.name, local_path,
                   self.config.get('config', 'hgroot'))


def run():
    try:
        SyncHg.run()
    except AbortException:
        pass
    except SyncError as e:
        # TODO: Colour would be nice here..
        print "Error: {0}".format(e)

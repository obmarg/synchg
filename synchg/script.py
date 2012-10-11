from plumbum import cli, local
from actions import SyncRemote, AbortException


class SyncHg(cli.Application):
    name = cli.SwitchAttr(
            ['n', '--name'],
            help='The name of the local repository.'
                 'Uses the current directory name by default'
            )

    def main(self, action, remote, path=None):
        if path:
            path = local.cwd / path
        else:
            path = local.cwd

        if not self.name:
            self.name = (local.cwd / path).basename

        if action == 'sync':
            SyncRemote(remote, self.name, path)
        else:
            raise Exception('Unrecognised action: {0}'.format(action))


def run():
    try:
        SyncHg.run()
    except AbortException:
        pass

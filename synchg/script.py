from plumbum import cli
from actions import SyncRemote


class SyncHg(cli.Application):
    name = cli.SwitchAttr(
            ['n', '--name'],
            help='The name of the local repository.'
                 'Uses the current directory name by default'
            )

    def main(self, action, remote):
        if action == 'sync':
            SyncRemote(remote, self.name)
        else:
            raise Exception('Unrecognised action: {0}'.format(action))


def run():
    SyncHg.run()

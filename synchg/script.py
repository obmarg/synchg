from plumbum import cli, local
from actions import SyncRemote, AbortException, SyncError


class SyncHg(cli.Application):
    name = cli.SwitchAttr(
            ['n', '--name'],
            help='The name of the repository.'
                 'Uses the directory name by default'
            )

    def main(self, remote_host, local_path=None):
        if local_path:
            local_path = local.cwd / local_path
        else:
            local_path = local.cwd

        if not self.name:
            self.name = local_path.basename

        SyncRemote(remote_host, self.name, local_path)


def run():
    try:
        SyncHg.run()
    except AbortException:
        pass
    except SyncError as e:
        # TODO: Colour would be nice here..
        print "Error: {0}".format(e)

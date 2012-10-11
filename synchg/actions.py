import plumbum
from plumbum import SshMachine
from plumbum.cmd import hg
from repo import Repo


def SyncRemote(host, name, localpath):
    '''
    Syncs a remote repository

    :param host:        The hostname of the remote repository
    :param name:        The name of the project that is being synced
    :param localpath:   A plumbum path to the local repository
    '''
    print "Syncing remote repo {0} on {1}".format(name, host)
    with SshMachine(host) as remote:
        with plumbum.local.cwd(localpath):
            with remote.cwd(remote.cwd / remote.env['HGROOT'] / name):
                _DoSync(Repo(hg, host), Repo(remote['hg']))


def _DoSync(local, remote):
    '''
    Function that actually handles the syncing after everything
    has been set up

    :param local:   The local repository
    :param remote:  The remote repository
    '''
    print "Syncing to changeset {0} on branch {1}".format(
            local.currentRev, local.branch
            )

    # Pop any patches on the remote before we begin
    remote.PopPatch()

    with local.CleanMq():
        outgoings = local.GetOutgoings()
        if outgoings:
            incomings = local.GetIncomings()
            if incomings:
                print "Stripping {0} changesets from remote".format(
                        len(incomings)
                        )
                # TODO: Probably want to provide a prompt here
                remote.Strip(incomings)
            print "Pushing to remote"
            local.PushToRemote()

    print "Updating remote"
    remote.Update(local.currentRev)

    appliedPatch = local.GetLastAppliedPatch()
    if appliedPatch:
        # TODO: would be good to do a sanity check on the state of
        #       the mq repo etc. here...
        local.CommitMq()
        local.PushMqToRemote()
        print "Pushed mq repository to remote"
        remote.UpdateMq()
        remote.PushPatch(appliedPatch)
        print "Updated remote mq repository and applied patches"
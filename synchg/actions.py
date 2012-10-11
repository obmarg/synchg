from six import print_
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
    print "Syncing remote repo %s on %s" % (name, host)
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
    print_( "Syncing to changeset %s on branch %s",
            local.currentRev, local.branch
            )
    #TODO: Totally want to log all the output from the remote commands
    #       particularly the strip ones etc.  would be much safer
    outgoings = local.GetOutgoings()

    # Pop any patches on the remote before we begin
    remote.PopPatch()

    if len(outgoings) > 0:
        incomings = local.GetIncomings()
        if len(incomings) > 0:
            print "Stripping %i changesets from remote" % (len(incomings))
            # TODO: Also probably want the ability to provide a prompt here
            remote.strip(incomings)
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

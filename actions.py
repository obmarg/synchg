from six import print_
import plumbum
from plumbum import SshMachine
from plumbum.cmd import hg
from repo import Repo


def SyncRemote(host, project):
    '''
    Syncs a remote repository

    :param host:    The hostname of the remote repository
    :param project: The name of the project that is being synced
    '''
    print "Syncing remote repo %s on %s" % (project, host)
    with SshMachine() as remote:
        with remote.cwd(remote.cwd / remote.env['HGROOT']):
            _DoSync(host, Repo(hg, host), Repo(remote['hg']))


def _DoSync(host, local, remote):
    '''
    Function that actually handles the syncing after everything
    has been set up

    :param host:    The hostname of the remote repository
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
        #TODO: Probably want to check if there are any local unsyned
        #       changes.
        #       It'll cause future commands to fail in a rather ugly way.
        #       so if we could die here with a sane message it'd be great
        incomings = local.GetIncomings()
        if len(incomings) > 0:
            print "Stripping %i changesets from remote" % (len(incomings))
            # This next command can fail if there's local changes (so can
            # most probably ), so maybe want to -f it?
            # TODO: Also probably want the ability to provide a prompt here
            remote.strip(incomings)
        print "Pushing to remote"
        local.PushToRemote()
        print "Updating remote"

    remote.Update(local.currentRev)

    appliedPatch = local.GetLastAppliedPatch()
    if appliedPatch:
        #TODO: Could check if qinit -c has been run here.
        #      Same with remote host.
        #      Would also be good to ensure that the patches remote has
        #      been setup, but for now just assume that it has

        #TODO: Also want to wrap these run's in Repo class
        local.CommitMq()
        local.PushMqToRemote()
        print "Pushed mq repository to %s" % host
        remote.UpdateMq()
        remote.PushPatch(appliedPatch)
        print "Updated remote mq repository and applied patches"

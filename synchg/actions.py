import sys
import plumbum
from plumbum import SshMachine
from repo import Repo
from utils import yn

if sys.platform.startswith('win'):
    from puttyssh import PuttySshMachine as SshMachine

class AbortException(Exception):
    ''' An exception that's thrown when a user chooses to abort '''
    pass


class SyncError(Exception):
    '''
    An exception that's thrown when a non-exceptional error occurs.  This
    exception is usually accompanied by an error message and should probably
    be caught and the backtrace suppressed.
    '''
    pass


def SyncRemote(host, name, localpath, remote_root):
    '''
    Syncs a remote repository

    :param host:        The hostname of the remote repository
    :param name:        The name of the project that is being synced
    :param localpath:   A plumbum path to the local repository
    :param remote_root: The path to the remote root src dir
    '''
    print "Sync {0} -> {1}".format(name, host)
    with SshMachine(host) as remote:
        with plumbum.local.cwd(localpath):
            local = Repo(plumbum.local, host)
            rpath = remote.cwd / remote_root / name
            if not rpath.exists():
                print "Remote repository can't be found."
                if yn('Do you want to create a clone?'):
                    local.Clone('ssh://{0}/{1}/{2}'.format(
                        host, remote_root, name
                        ))
                else:
                    raise AbortException
            with remote.cwd(rpath):
                _DoSync(local, Repo(remote))


def _DoSync(local, remote):
    '''
    Function that actually handles the syncing after everything
    has been set up

    :param local:   The local repository
    :param remote:  The remote repository
    '''
    # First, check the state of each repository
    if remote.summary.commit.modified:
        # Changes might be lost on remote...
        raise SyncError('Remote repository has uncommitted changes')

    lsummary = local.summary
    if lsummary.commit.modified:
        print "Local repository has uncommitted changes."
        if lsummary.mq.applied:
            # We can't push/pop patches to check remote is
            # in sync if we've got local changes, so prompt to refresh.
            if yn('Do you want to refresh the current patch?'):
                local.RefreshMq()
            else:
                print "Ok.  Please run again after dealing with changes."
                raise AbortException
        else:
            # If we're not doing an mq sync, we can happily ignore
            # these changes, but probably want to make sure that's
            # what the user wants...
            if not yn('Do you want to ignore these changes?'):
                print "Ok.  Please run again after dealing with changes."
                raise AbortException

    # Pop any patches on the remote before we begin
    remote.PopPatch()

    with local.CleanMq():
        if local.outgoings:
            incomings = local.incomings
            if incomings:
                # Don't want to be creating new remote heads when we push
                print "Changesets will be stripped from remote:"
                for hash, desc in incomings:
                    if len(desc) > 50:
                        desc = desc[:47] + '...'
                    print "  {0}  {1}".format(hash[:6], desc)
                if not yn('Do you want to continue?'):
                    raise AbortException()
                remote.Strip(incomings)
            print "Pushing to remote"
            local.PushToRemote()

    print "Updating remote"
    remote.Update(local.currentRev)

    appliedPatch = local.GetLastAppliedPatch()
    if appliedPatch:
        print "Syncing mq repos"
        local.CommitMq()
        local.PushMqToRemote()
        print "Updating remote mq repo"
        remote.UpdateMq()
        remote.PushPatch(appliedPatch)

    print "Ok!"

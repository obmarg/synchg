'''
This module provides the actual syncing functionality for SyncHg.  It's
functions can be called by imported and called by other libraries if they wish
to make use of SyncHg functionality.
'''

import plumbum
from remote import RemoteMachine
from repo import Repo
from utils import yn


class AbortException(Exception):
    '''
    An exception that's thrown when a user chooses to abort.  This should be
    caught and ignored at the start of the program to allow users to abort at
    prompts
    '''
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
    Syncs a remote repository.  This function should be called to kick off a
    sync

    :param host:        The hostname of the remote repository
    :param name:        The name of the project that is being synced.
                        This parameter will be appended to the remote_root
                        to find the remote repository.
    :param localpath:   A plumbum path to the local repository
    :param remote_root: The path to the parent directory of the
                        remote repository
    '''
    print "Sync {0} -> {1}".format(name, host)
    with RemoteMachine(host) as remote:
        with plumbum.local.cwd(localpath):
            local = Repo(plumbum.local, host)
            remote_path = remote_root + '/' + name
            _SanityCheckRepos(local, host, remote_path, remote)
            with remote.cwd(remote.cwd / remote_path):
                _DoSync(local, Repo(remote))


def _SanityCheckRepos(local_repo, host, remote_path, remote):
    '''
    Does a sanity check of the repositories, and attempts
    to fix any problems found.

    This includes cloning the repository, setting up remotes
    and setting up mq repositories.

    It's expected that the local path will be set up by this point

    :param local_repo:  A Repo object for the local repository
    :param host:        The hostname of the remote repo
    :param remote_path: The path to the remote repository as a string
    :param remote:      A plumbum machine for the remote machine
    '''
    patch_dir = plumbum.local.cwd / '.hg' / 'patches'
    if patch_dir.exists():
        if not (patch_dir / '.hg').exists():
            # Seems mq --init hasn't been run.  Run it.
            local_repo.InitMq()
            local_repo.CommitMq()

    # Check if the remote exists, and clone it if not
    hg_remote_path = 'ssh://{0}/{1}'.format(host, remote_path)
    rpath = remote.cwd / remote_path
    if not rpath.exists():
        print "Remote repository can't be found."
        if yn('Do you want to create a clone?'):
            local_repo.Clone(hg_remote_path)
        else:
            raise AbortException

    # Check if remote paths are set up properly
    if host not in local_repo.config.remotes:
        local_repo.config.AddRemote(host, hg_remote_path)

    if host not in local_repo.mqconfig.remotes:
        local_repo.mqconfig.AddRemote(host, hg_remote_path + '/.hg/patches')

    # TODO: Would probably be good to check that the remotes aren't
    #       pointing at the wrong address as well

    # Finally, check if the mq repository needs cloned
    if patch_dir.exists() and not (rpath / '.hg' / 'patches').exists():
        local_repo.CloneMq(hg_remote_path)


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

    appliedPatch = local.lastAppliedPatch
    if appliedPatch:
        print "Syncing mq repos"
        local.CommitMq()
        local.PushMqToRemote()
        print "Updating remote mq repo"
        remote.UpdateMq()
        remote.PushPatch(appliedPatch)

    print "Ok!"

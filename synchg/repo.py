import re
from collections import namedtuple
from plumbum import ProcessExecutionError

__all__ = ['Repo']


def CleanMq(func):
    '''
    Decorator that ensures a function is always with no patches applied
    Should only be applied on Repo methods

    Params:
        func - The function to decorate
    '''
    def InnerFunc(self, *pargs):
        revertTo = self.GetLastAppliedPatch()
        try:
            self.PopPatch()
            return func(self, *pargs)
        finally:
            if revertTo:
                self.PushPatch(revertTo)
    return InnerFunc


class UncommitedChangesError(Exception):
    pass


class Repo(object):
    SummaryInfo = namedtuple('SummaryInfo', ['commit', 'update', 'mq'])
    CommitChangeInfo = namedtuple(
            'CommitChangeInfo',
            ['modified', 'unknown']
            )
    MqAppliedInfo = namedtuple('MqAppliedInfo', ['applied', 'unapplied'])

    def __init__(self, hg, remote=None):
        '''
        Constructor

        :param hg:      The plumbum hg object to use (can be local or remote)
        :param remote:  The remote hostname to use
        '''
        self.hg = hg
        self.remote = remote
        # Get the summary, to check if we have any un-committed changes
        summary = self.GetSummary()
        if summary.commit.modified:
            raise UncommitedChangesError()
            # TODO: Prompt the user to commit/refresh/shelve changes or abort
        self.CheckCurrentRev()
        self.prevLevel = None

    def GetSummary(self):
        '''
        Gets info from hg summary

        :return:  A SummaryInfo namedtuple containing CommitChangeInfo &
                  MqAppliedInfo
        '''
        commitData = Repo.CommitChangeInfo(0, 0)
        mqData = None
        commitRegexp = re.compile(
                r'^commit:\s+((\d+) modified(, (\d+) unknown)?)?'
                )
        mqRegexp = re.compile(r'^mq:\s+((\d+) applied, (\d+) unapplied)?')
        lines = self.hg('summary').split()
        for line in lines:
            match = commitRegexp.search( line )
            if match:
                commitData = Repo.CommitChangeInfo(*match.group( 2, 4 ))
            match = mqRegexp.search( line )
            if match:
                mqData = Repo.MqAppliedInfo(*match.group(2, 3))
        return Repo.SummaryInfo(commitData, None, mqData)

    @CleanMq
    def CheckCurrentRev( self ):
        ''' Gets the current revision and branch and stores it '''

        revMatch = re.search(
            r'^(\w{12})\+?\s+(.*)\s*$',
            self.hg('id', '-i', '-b')
            )
        if revMatch is None:
            raise Exception("Could not get current revision using hg id")
        self.currentRev, self.branch = revMatch.group(1, 2)

    def _RunListCommand(self, command, headerLines=0):
        '''
        Runs an hg command that gets a list (outgoing, incoming etc.)

        :param command:     The plumbum command object to run
        :param headerLines: The number of lines to chop off the top of
                            the output
        '''
        try:
            lines = command().split()
            if headerLines == 0:
                return lines
            if len(lines) < headerLines:
                raise Exception("Unexpected number of lines from hg command")
            return lines[headerLines:]
        except ProcessExecutionError as e:
            if e.retcode != 1:
                # retcode of 1 just means there's nothing in the list,
                # so ignore it
                raise
        return []

    @CleanMq
    def GetOutgoings(self):
        '''
        Gets the outgoing changesets.

        :returns: A list of changeset hashes for the outgoing changesets
        '''
        assert self.remote
        return self._RunListCommand(
                self.hg[ 'outgoing', '-b', self.branch, '-r', self.currentRev,
                         '--template', '"{node}\\n"', self.remote
                         ],
                headerLines=2
                )

    @CleanMq
    def GetIncomings(self):
        '''
        Gets the incoming changesets.

        :returns: A list of changeset hashes for the incoming changesets
        '''
        assert self.remote
        return self._RunListCommand(
                self.hg[ 'incoming', '-b', self.branch,
                         '--template', '"{node}\\n"', self.remote
                         ],
                headerLines=2
                )

    def GetLastAppliedPatch(self):
        '''
        Gets the last applied mq patch (if there is one)
        :returns: A single mq patch name (or None)
        '''
        # TODO: Want this to handle mq being disabled...
        patches = self._RunListCommand(self.hg['qapplied'])
        if len(patches):
            return patches[-1]
        else:
            return None

    @CleanMq
    def PushToRemote( self ):
        ''' Pushes to the remote repository '''
        assert self.remote
        self.hg('push', '-b', self.branch, '-r', self.currentRev, self.remote)

    def PopPatch(self, patch=None):
        '''
        Pops an mq patch on local repo.

        :param patch: Name of the patch to pop.  If None, all will be popped
        '''
        # Check there are some patches applied
        level = self.GetLastAppliedPatch()
        if level:
            if patch is None:
                patch = '-a'
            self.hg('qpop', patch)

    def PushPatch(self, patch=None):
        '''
        Pushes an mq patch on local repo

        :param patch: Name of the patch to push.  If None, all will be pushed
        '''
        if patch is None:
            patch = '-a'
        self.hg('qpush', patch)

    @CleanMq
    def Strip(self, changesets):
        '''
        Strips changesets from the repo with the strip command

        :param changesets:  A list of changeset ids to strip
        '''
        self.hg('strip', *changesets)

    @CleanMq
    def Clone(self, destination, remoteName=None):
        '''
        Clones the repository to a different location
        @param: destination     The destination clone path
        @param: remoteName      If set a remote will be created with this name
        '''
        # TODO: This one will probably need moved elsewhere
        self.hg('clone', '.', destination)
        if remoteName:
            #TODO: set up remote name
            pass
        # This all needs to go in different function, but:
        # Need to hg update on remote
        # Then hg qinit -c (on remote, and possibly local)
        # then (if not already done) add mq remote
        # then local hg commit -mq if needed
        # then hg push --mq glencaple etc.

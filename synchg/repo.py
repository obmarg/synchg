import re
from collections import namedtuple
from contextlib import contextmanager
from plumbum import ProcessExecutionError

__all__ = ['Repo']


class Repo(object):
    SummaryInfo = namedtuple('SummaryInfo', ['commit', 'mq'])
    CommitChangeInfo = namedtuple(
            'CommitChangeInfo',
            ['modified', 'unknown']
            )
    MqAppliedInfo = namedtuple('MqAppliedInfo', ['applied', 'unapplied'])

    # Template Parameter for hg log-style commands
    HgTemplateParam = '{node}\\t{desc|firstline}\\n'

    # Contains details of a changeset
    ChangesetInfo = namedtuple('ChangsetInfo', ['hash', 'desc'])
    ChangesetInfoRegexp = re.compile(r'^(?P<hash>\w+)\t(?P<desc>.*)$')

    def __init__(self, hg, remote=None):
        '''
        Constructor

        :param hg:      The plumbum hg object to use (can be local or remote)
        :param remote:  The remote hostname to use
        '''
        self.hg = hg
        self.remote = remote
        # Get the summary, to check if we have any un-committed changes
        self.CheckCurrentRev()
        self.prevLevel = None

    @contextmanager
    def CleanMq(self):
        '''
        Returns a context manager that keeps the mq repository clean
        for it's lifetime
        '''
        revertTo = self.GetLastAppliedPatch()
        self.PopPatch()
        yield
        if revertTo:
            self.PushPatch(revertTo)

    def _CleanMq(func):
        '''
        Decorator that ensures a function is always run with no patches applied
        Should only be applied on Repo methods

        Params:
            func - The function to decorate
        '''
        def InnerFunc(self, *pargs):
            with self.CleanMq():
                return func(self, *pargs)
        return InnerFunc

    @property
    def summary(self):
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
        return Repo.SummaryInfo(commitData, mqData)

    @_CleanMq
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
            lines = command().splitlines()
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

    def _GetChangesetInfoList(self, *pargs, **kwargs):
        '''
        Utility function that calls _RunListCommand and filters the results
        through ChangesetInfoRegexp

        :returns:   A list of ChangesetInfo namedtuples
        '''
        lines = self._RunListCommand(*pargs, **kwargs)
        matches = (self.ChangesetInfoRegexp.match(line) for line in lines)
        return [self.ChangesetInfo(**match.groupdict()) for match in matches]

    @_CleanMq
    def GetOutgoings(self):
        '''
        Gets the outgoing changesets.

        :returns: A list of changeset hashes for the outgoing changesets
        '''
        assert self.remote
        return self._GetChangesetInfoList(
                self.hg[ 'outgoing', '-b', self.branch, '-r', self.currentRev,
                         '--template', self.HgTemplateParam, self.remote
                         ],
                headerLines=2
                )

    @_CleanMq
    def GetIncomings(self):
        '''
        Gets the incoming changesets.

        :returns: A list of changeset hashes for the incoming changesets
        '''
        assert self.remote
        return self._GetChangesetInfoList(
                self.hg[ 'incoming', '-b', self.branch,
                         '--template', self.HgTemplateParam, self.remote
                         ],
                headerLines=2
                )

    def GetLastAppliedPatch(self):
        '''
        Gets the last applied mq patch (if there is one)
        :returns: A single mq patch name (or None)
        '''
        try:
            patches = self._RunListCommand(self.hg['qapplied'])
            if patches:
                return patches[-1]
        except ProcessExecutionError as e:
            if e.retcode != 255:
                # 255 means mq is probably disabled
                raise
        return None

    @_CleanMq
    def PushToRemote(self):
        ''' Pushes to the remote repository '''
        assert self.remote
        self.hg('push', '-b', self.branch, '-r', self.currentRev, self.remote)

    def PushMqToRemote(self):
        ''' Pushes mq repo to the remote '''
        assert self.remote
        try:
            self.hg('push', '--mq', self.remote)
        except ProcessExecutionError as e:
            if e.retcode != 1:
                #1 just means there's no outgoings
                raise

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

    @_CleanMq
    def Strip(self, changesets):
        '''
        Strips changesets from the repo with the strip command

        :param changesets:  A list of ChangesetInfo's to strip
        '''
        self.hg('strip', *[cs.hash for cs in changesets])

    @_CleanMq
    def Update(self, changeset):
        '''
        Updates to a specific changeset

        :param changeset:   The changeset id to update to
        '''
        # TODO: Seems a bit inconsistent that this takes a changeset id/hash
        # and other functions take a ChangesetInfo.  Maybe fix that
        self.hg('update', changeset)

    def UpdateMq(self):
        '''
        Updates the mq repository
        '''
        self.hg('update', '--mq')

    def CommitMq(self, msg=None):
        '''
        Commits the mq repository

        :param msg:     An optional commit message
        '''
        args = []
        if msg:
            args = ['-m', 'synchg-commit']
        try:
            self.hg('commit', '--mq', *args)
        except ProcessExecutionError as e:
            if e.retcode != 1:
                #1 just means there's no changes
                raise

    @_CleanMq
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

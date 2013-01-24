import re
import functools
import copy
from collections import namedtuple
from ConfigParser import ConfigParser
from contextlib import contextmanager
from plumbum import ProcessExecutionError

__all__ = ['Repo']


class Repo(object):
    '''
    This class provides an abstraction around running commands on a mercurial
    repository.  It can be used against either a local or remote repository
    depending on the ``machine`` parameter to the constructor.
    '''

    SummaryInfo = namedtuple('SummaryInfo', ['commit', 'mq'])
    CommitChangeInfo = namedtuple(
            'CommitChangeInfo',
            ['modified', 'unknown']
            )
    MqAppliedInfo = namedtuple('MqAppliedInfo', ['applied', 'unapplied'])

    # Template Parameter for hg log-style commands
    HgTemplateParam = '{node}\\t{desc|firstline}\\n'

    # Contains details of a changeset
    ChangesetInfo = namedtuple('ChangesetInfo', ['hash', 'desc'])
    ChangesetInfoRegexp = re.compile(r'^(?P<hash>\w+)\t(?P<desc>.*)$')

    # Should be set to true during tests.
    Testing = False

    def __init__(self, machine, remote=None):
        '''
        :param machine:     The plumbum machine object to use
                            (can be a local machine or remote machine)
        :param remote:      The name of the remote repo to be used by
                            push, pull and other operations.
        '''
        self.machine = machine
        self.hg = self.machine['hg']
        self.remote = remote
        try:
            self._path = copy.copy(self.machine.cwd)
        except:
            # This excepts during testing, so ignore it
            if self.Testing:
                self._path = self.machine.cwd
            else:
                raise
        self._currentRev = self._branch = None
        self.prevLevel = None
        self._config = self._mqconfig = None

    @contextmanager
    def CleanMq(self):
        '''
        Returns a context manager that keeps the mq repository clean
        for it's lifetime
        '''
        revertTo = self.lastAppliedPatch
        self.PopPatch()
        yield
        if revertTo:
            self.PushPatch(revertTo)

    def _CleanMq(func):
        '''
        Decorator that ensures a function is always run with no patches applied
        Should only be applied on Repo methods

        :params func:   The function to decorate
        '''
        @functools.wraps(func)
        def InnerFunc(self, *pargs):
            with self.CleanMq():
                return func(self, *pargs)
        return InnerFunc

    @property
    def summary(self):
        '''
        Gets info from hg summary

        :return:    A :class:`SummaryInfo` containing :class:`CommitChangeInfo`
                    & :class:`MqAppliedInfo`
        '''
        commitData = Repo.CommitChangeInfo(0, 0)
        mqData = Repo.MqAppliedInfo(0, 0)
        commitRegexp = re.compile(
                r'^commit:\s+((\d+) modified(, (\d+) unknown)?)?'
                )
        mqRegexp = re.compile(
                r'^mq:\s+((\d+) applied,?\s*)?((\d+) unapplied)?'
                )
        lines = self.hg('summary').splitlines()
        for line in lines:
            match = commitRegexp.search( line )
            if match:
                commitData = Repo.CommitChangeInfo(
                        int(match.group(2) or 0), int(match.group(4) or 0)
                        )
            match = mqRegexp.search( line )
            if match:
                mqData = Repo.MqAppliedInfo(
                        int(match.group(2) or 0), int(match.group(4) or 0)
                        )
        return Repo.SummaryInfo(commitData, mqData)

    @property
    def currentRev(self):
        '''
        Gets the current revision
        This property is cached, so it may be out of date

        :returns:   A string containing the current revision hash
        '''
        if not self._currentRev:
            self._CheckCurrentRev()
        return self._currentRev

    @property
    def branch(self):
        '''
        Gets the current branch
        This property is cached, so it may be out of date

        :returns:   A string containing the current branch name
        '''
        if not self._branch:
            self._CheckCurrentRev()
        return self._branch

    @property
    def config(self):
        '''
        Gets the configuration for this repository

        :returns: A ``RepoConfig`` class
        '''
        if not self._config:
            self._config = RepoConfig(self._path)
        return self._config

    @property
    def mqconfig(self):
        '''
        Gets the configuration for the mq repository

        :returns A ``RepoConfig`` class
        '''
        if not self._mqconfig:
            self._mqconfig = RepoConfig(self._path / '.hg' / 'patches')
        return self._mqconfig

    @_CleanMq
    def _CheckCurrentRev( self ):
        ''' Gets the current revision and branch and stores it '''

        revMatch = re.search(
            r'^(\w{12})\+?\s+(.*)\s*$',
            self.hg('id', '-i', '-b')
            )
        if revMatch is None:
            raise Exception("Could not get current revision using hg id")
        self._currentRev, self._branch = revMatch.group(1, 2)

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

        :returns:   A list of :class:`ChangesetInfo`
        '''
        lines = self._RunListCommand(*pargs, **kwargs)
        matches = (self.ChangesetInfoRegexp.match(line) for line in lines)
        return [self.ChangesetInfo(**match.groupdict()) for match in matches]

    @property
    @_CleanMq
    def outgoings(self):
        '''
        Gets the outgoing changesets to `self.remote`

        :returns:   A list containing :class:`ChangesetInfo` that represent
                    the current outgoing changesets
        '''
        assert self.remote
        return self._GetChangesetInfoList(
                self.hg[ 'outgoing', '-b', self.branch, '-r', self.currentRev,
                         '--template', self.HgTemplateParam, self.remote
                         ],
                headerLines=2
                )

    @property
    @_CleanMq
    def incomings(self):
        '''
        Gets the incoming changesets from `self.remote`

        :returns:   A list containing :class:`ChangesetInfo` that represent
                    the current incoming changesets
        '''
        assert self.remote
        return self._GetChangesetInfoList(
                self.hg[ 'incoming', '-b', self.branch,
                         '--template', self.HgTemplateParam, self.remote
                         ],
                headerLines=2
                )

    @property
    def lastAppliedPatch(self):
        '''
        Gets the last applied mq patch (if there is one)

        :returns: A single mq patch name (or None)
        '''
        try:
            return self.hg('qtop').strip()
        except ProcessExecutionError as e:
            if e.retcode not in [1, 255]:
                # 1 means no patches
                # 255 means mq is probably disabled
                raise
        return None

    @_CleanMq
    def PushToRemote(self):
        ''' Pushes to the remote repository at `self.remote`'''
        assert self.remote
        self.hg('push', '-b', self.branch, '-r', self.currentRev, self.remote)

    def PushMqToRemote(self):
        ''' Pushes the mq repo to the remote at `self.remote` '''
        assert self.remote
        try:
            self.hg('push', '--mq', self.remote)
        except ProcessExecutionError as e:
            if e.retcode != 1:
                #1 just means there's no outgoings
                raise

    def PopPatch(self, patch=None):
        '''
        Pops mq patch(es)

        :param patch:   Name of the patch to pop to.
                        If None, all will be popped
        '''
        # Check there are some patches applied
        level = self.lastAppliedPatch
        if level:
            if patch is None:
                patch = '-a'
            self.hg('qpop', patch)

    def PushPatch(self, patch=None):
        '''
        Pushes mq patch(es)

        :param patch:   Name of the patch to push to.
                        If None, all will be pushed
        '''
        if patch is None:
            patch = '-a'
        self.hg('qpush', patch)

    @_CleanMq
    def Strip(self, changesets):
        '''
        Strips changesets from this repository

        :param changesets:  A list of :class:`ChangesetInfo`
                            representing the changesets to strip
        '''
        self.hg('strip', *[cs.hash for cs in changesets])

    @_CleanMq
    def Update(self, changeset):
        '''
        Updates to a specific changeset

        :param changeset:   A changeset hash string, or
                            :class:`ChangesetInfo` representing
                            the changeset to update to
        '''
        if isinstance(changeset, self.ChangesetInfo):
            changeset = changeset.hash
        self.hg('update', changeset)

    def UpdateMq(self):
        '''
        Updates the mq repository to tip
        '''
        self.hg('update', '--mq')

    def RefreshMq(self):
        '''
        Refreshes the current mq patch
        '''
        self.hg('qrefresh')

    def CommitMq(self, msg=None):
        '''
        Commits the mq repository

        :param msg:     An optional commit message
        '''
        if not msg:
            msg = 'synchg-commit'
        try:
            self.hg('commit', '--mq', '-m', msg)
        except ProcessExecutionError as e:
            if e.retcode != 1:
                #1 just means there's no changes
                raise

    def InitMq(self):
        '''
        Initialises the mq repository
        '''
        self.hg('init', '--mq')

    @_CleanMq
    def Clone(self, destination, createRemote=True):
        '''
        Clones the repository to a different location

        :param destination:     The destination clone path
        :param createRemote:    If set a remote will be created in the local
                                hgrc with the name the class was initialised
                                with.
        '''
        remoteName = self.remote if createRemote else None
        self._DoClone(self.config, destination, remoteName)
        patches = self._path / '.hg' / 'patches'
        if patches.exists():
            self.CloneMq(destination, createRemote)

    def CloneMq(self, destination, createRemote=True):
        '''
        Clones the mq repository to a different location

        :param destination:     The destination path to the top-level remote
                                repository.  NOT the remote mq repository
        :param createRemote:    If set, a remote will be created in the local
                                mq hgrc with the name the class was initialised
                                with
        '''
        remoteName = self.remote if createRemote else None
        patches_path = self._path / '.hg' / 'patches'
        destination = destination + '/.hg/patches'
        with self.machine.cwd(patches_path):
            self._DoClone(self.mqconfig, destination, remoteName)

    def _DoClone(self, config, destination, remoteName):
        '''
        Actually performs a clone operation

        :param config:          A configuration object to update
        :param destination:     The destination clone path
        :param remoteName:      The name of the remote to create (if any)
        '''
        self.hg('clone', '.', destination)
        if remoteName:
            config.AddRemote(remoteName, destination)


class RepoConfig(object):
    '''
    This class provides an abstraction around repository configuration files
    '''

    def __init__(self, path):
        '''
        :param path:    Plumbum path to the repository
        '''
        self._config = ConfigParser()
        self._path = path / '.hg' / 'hgrc'
        if self._path.exists():
            self._config.readfp(self._path.open())
        else:
            self._config.add_section('paths')

    def AddRemote(self, name, destination):
        '''
        Adds a remote to the config, or overwrites if it already exists

        :param name:        The name of the remote
        :param destination: The destination path of the remote
        '''
        self._config.set('paths', name, destination)
        self._config.write(self._path.open('w'))

    @property
    def remotes(self):
        '''
        Property to get a dictionary of remotes
        '''
        return dict(self._config.items('paths'))



import re
from collections import namedtuple

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


class Repo(object):
    SummaryInfo = namedtuple('SummaryInfo', ['commit', 'update', 'mq'])
    CommitChangeInfo = namedtuple(
            'CommitChangeInfo',
            ['modified', 'unknown']
            )
    MqAppliedInfo = namedtuple('MqAppliedInfo', ['applied', 'unapplied'])

    def __init__(self, host):
        self.host = host
        # Get the summary, to check if we have any un-committed changes
        summary = self.GetSummary()
        if summary.commit.modified:
            raise Exception(
                    "Local mercurial repository has uncommited changes"
                    )
            # TODO: Prompt the user to commit/refresh/shelve changes or abort
        self.CheckCurrentRev()
        self.prevLevel = None

    def GetSummary(self):
        '''
        Get's info from hg summary
        @return  A SummaryInfo namedtuple ( containing other namedtuples )
        '''
        commitData = None
        mqData = None
        commitRegexp = re.compile(
                r'^commit:\s+((\d+) modified(, (\d+) unknown)?)?'
                )
        mqRegexp = re.compile(r'^mq:\s+((\d+) applied, (\d+) unapplied)?')
        lines = util.run('hg summary')
        for line in lines:
            match = commitRegexp.search( line )
            if match:
                commitData = Repo.CommitChangeInfo( *match.group( 2, 4 ) )
            match = mqRegexp.search( line )
            if match:
                mqData = Repo.MqAppliedInfo( *match.group( 2, 3 ) )
        return Repo.SummaryInfo(commitData, None, mqData)

    @CleanMq
    def CheckCurrentRev( self ):
        ''' Gets the current revision and branch and stores it '''

        revMatch = re.search(
            r'^(\w{12})\+?\s+(.*)\s*$',
            '\n'.join(util.run('hg id -i -b'))
            )
        if revMatch is None:
            raise Exception("Could not get current revision using hg id")
        self.currentRev, self.branch = revMatch.group(1, 2)

    def RunListCommand(self, command, headerLines=0):
        '''
        Runs an hg command that gets a list
        Params:
            command - The command to run
            headerLines - The number of lines to chop off the top of the output
        '''
        try:
            output = util.run(command, silent=True)
            if headerLines == 0:
                return output
            if len(output) < headerLines:
                raise Exception("Unexpected number of lines from hg command")
            return output[headerLines:]
        except util.RunError as e:
            if e.code != 1:
                # 1 just means there's no outgoings
                raise
        return []

    @CleanMq
    def GetOutgoings(self):
        '''
        Gets the outgoing changesets.
        Returns a list of changeset hashes
        '''
        return self.RunListCommand(
            'hg outgoing -b %s -r %s --template "{node}\\n" %s' % (
                    self.branch, self.currentRev, self.host
                    ),
            headerLines=2
            )

    @CleanMq
    def GetIncomings(self):
        '''
        Gets the incoming changesets.
        Returns a list of changeset hashes
        '''
        return self.RunListCommand(
            'hg incoming -b %s --template "{node}\\n" %s' % (
                    self.branch, self.host
                    ),
            headerLines=2
            )

    def GetLastAppliedPatch(self):
        '''
        Gets the last applied patch
        Returns a single hash (or None)
        '''
        ls = self.RunListCommand(
                'hg qapplied'
                )
        if len( ls ):
            return ls[-1]
        else:
            return None

    @CleanMq
    def PushToRemote( self ):
        ''' Pushes to the remote repository '''
        util.run( 'hg push -b %s -r %s %s' % (
            self.branch, self.currentRev, self.host
            ) )

    def PopPatch(self, patch=None):
        '''
        Pops an mq patch on local repo.
        Params:
            patch - The patch to pop.  If None, all will be popped
        '''
        # Check there are some patches applied
        level = self.GetLastAppliedPatch()
        if level:
            if patch is None:
                patch = '-a'
            util.run('hg qpop %s' % patch)

    def PushPatch( self, patch=None ):
        '''
        Pushes an mq patch on local repo
        Params:
            patch - The patch to push.  If None, all will be pushed
        '''
        if patch is None:
            patch = '-a'
        util.run('hg qpush %s' % patch)

    @CleanMq
    def Clone( self, destination, remoteName=None ):
        '''
        Clones the repository to a different location
        @param: destination     The destination clone path
        @param: remoteName      If set a remote will be created with this name
        '''
        util.run('hg clone . "%s"' % destination)
        if remoteName:
            #TODO: set up remote name
            pass
        # This all needs to go in different function, but:
        # Need to hg update on remote
        # Then hg qinit -c (on remote, and possibly local)
        # then (if not already done) add mq remote
        # then local hg commit -mq if needed
        # then hg push --mq glencaple etc.

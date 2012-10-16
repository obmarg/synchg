'''
This file contains definitions neccesary to make use of this library with
putty, as the plumbum SSH code doesn't work too well with putty by default.

This is all a bit of a hack, and probably won't work as well as standard plumbum,
but hopefully this code can be discarded at some point, when the bug has been fixed.
'''

import re
from plumbum import local
from plumbum.commands import run_proc, shquote
from plumbum.remote_machine import SshMachine, Workdir

class FakeShellSession(object):
    '''
    This class implements the same interface as ``plumbum.session.ShellSession``, but doesn't
    actually represent a shell session.  Instead, it runs all commands individually.
    
    This adds a lot of overhead, but allows us to work around the fact that
    shell sessions don't play too nicely with putty.  
    '''

    def __init__(self, remote):
        self._remote = remote

    def __enter__(self):
        return self

    def __exit(self, t, v, tb):
        pass

    def alive(self):
        # Fake shell is always 'alive'
        return True

    def close(self):
        pass

    def popen(self, cmd):
        return self._remote.popen(cmd.split(' '), via_shell=True)

    def run(self, cmd, retcode = 0):
        return run_proc(self.popen(cmd), retcode)


class FakeWorkDir(Workdir):
    '''
    Hack to remove the dependency on shell sessions.  Probably doesn't work great, but
    as a temporary hack it should do the job
    '''
    PwdRegexp = re.compile('__START__\s+(.*?)\s+__END__')

    def __init__(self, remote):
        self.remote = remote
        self._path = remote._cwd

    def chdir(self,newdir):
        output = self.remote._session.run(
                "cd %s && echo '__START__' && pwd && echo '__END__'" % (shquote(newdir),)
                )
        assert output[0] == 0
        match = self.PwdRegexp.search(output[1])
        self._path = match.group(1)
        self.remote._cwd = self._path


class PuttySshMachine(SshMachine):
    '''
    This class inherits from ssh_machine, but overrides various bits to make it work with
    putty.
    '''

    def __init__(self, *pargs, **kwargs):
        self._finished_init = False
        if 'ssh_command' not in kwargs:
            kwargs['ssh_command'] = local['plink']
        if 'scp_command' not in kwargs:
            kwargs['scp_command'] = local['pscp']
        super(PuttySshMachine, self).__init__(*pargs, **kwargs)
        self._finished_init = True
        self._cwd = str(self.cwd)
        self.cwd = FakeWorkDir(self)

    def tunnel(self, *pargs, **kwargs):
        # Very much doubt this will work, so just disable it.
        raise NotImplementedError()

    def session(self, isatty=False):
        return FakeShellSession(self)

    def popen(self, args, ssh_opts = (), via_shell=False, **kwargs):
        if via_shell and not self._finished_init:
            # Just do stuff ourselves rather than letting the base class
            # access things that haven't been created
            cmdline = []
            cmdline.extend(ssh_opts)
            cmdline.append(self._fqhost)
            if isinstance(args, (tuple, list)):
                cmdline.extend(args)
            else:
                cmdline.append(args)
            return self._ssh_command[tuple(cmdline)].popen(**kwargs)
        return super(PuttySshMachine, self).popen(args, ssh_opts, **kwargs)
            


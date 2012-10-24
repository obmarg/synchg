import sys
from plumbum import SshMachine, PuttyMachine

_WIN32 = sys.platform.startswith('win')


def RemoteMachine(*pargs, **kwargs):
    '''
    Remote machine constructor function.  Forwards all arguments on to the
    appropriate constructor for this platform.  On windows this is
    ``plumbum.PuttyMachine`` and on other platforms `plumbum.SshMachine`
    '''
    if _WIN32:
        return PuttyMachine(*pargs, **kwargs)
    else:
        return SshMachine(*pargs, **kwargs)



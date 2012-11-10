Ever had to keep two mercurial repositories on different machines in sync?
Mercurials push & pull help to make this fairly easy, but if you make use of
mercurial queues or the histedit extension then it can quickly become tedious.
That's where synchg comes in.  

Synchg intends to make syncing two mercurial repositories as simple as
possible.  Simply run a command, and synchg will take care of the rest.

Requirements
============

Python 2.7 & Mercurial 2.3 are recommended, though others will probably work.

Synchg depends on these python packages:

* `Plumbum <https://github.com/tomerfiliba/plumbum>`_
* `Clint <https://github.com/kennethreitz/clint>`_

It also requires:

* An ssh client on the path (putty on windows, openssh compatible on other
  platforms)
* Access to an SSH server on the remote machine(s)
* An ssh private key loaded in an ssh agent (pagaent on windows, ssh-agent on
  other platforms)
* That the `mq <http://mercurial.selenic.com/wiki/MqExtension>`_ extension is
  enabled on the remote machine(s)

Installation
=============

Synchg and it's python dependencies can be installed via pip::
  
  $ pip install synchg

Using SyncHg
=============

The synchg script should be run from the command line::

  $ synchg remote_host [local_path=None]

Where ``remote_host`` is the host you wish to sync with and ``local_path`` is
the optional path to the local mercurial repository (if missing, the current
directory will be assumed)

Information on more options can be found by running::

  $ synchg --help

.. CAUTION::

    Synchg regards remote repositories as "slaves" and will strip out any
    changesets it finds that are not in the local repository.  You will be
    prompted before this happens, but the script will be unable to continue if
    you don't answer yes.

Configuration 
---------------

On first run of synchg you will be prompted with some configuration options:

Remote source directory
    This is the path on the remote under which all your repositories should be
    found.
    For example, if you have repositories at ``/repo/one/`` and ``/repo/two/``
    then you would set this to ``/repo/``

If you want to change the configuration of synchg, then simply run ``synchg
-c`` to run the config process again.

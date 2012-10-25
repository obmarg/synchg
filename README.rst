Ever had to keep two mercurial repositories on different machines in sync?
Mercurials push & pull help to make this fairly easy, but if you make use of
mercurial queues or the histedit extension then it can quickly become tedious.
That's where synchg comes in.  

Synchg intends to make syncing two mercurial repositories as simple as possible.  Simply run a command, and synchg will take care of the rest.

Requirements
============

Python 2.7 & Mercurial 2.3 are recommended, though others will probably work.

Synchg depends on these python packages:

* `Plumbum <https://github.com/tomerfiliba/plumbum>`_
* `Clint <https://github.com/kennethreitz/clint>`_

It also requires:

* Access to an SSH server on the remote machine(s)
* That the `mq <http://mercurial.selenic.com/wiki/MqExtension>`_ extension is
  enabled on the remote machine(s)

Installation
=============

Synchg and it's python dependencies can be installed via pip::
  
  $ pip install synchg

Using SyncHg
=============

Before using synchg on a repository you should ensure that your environment is
set up correctly.  If you intend to use mq patches with synchg, then you should
run ``hg init --mq`` on each local repository before you attempt to use it with
synchg.

It's recommended that you use synchg to make the initial clone to your remote
machine. This way it can take steps to add necessary settings to the local
repository.  However, if you wish to use synchg with an existing clone of your
repository, then read the section below entitled
`Using With Existing Clones`_.

Running The Script
------------------

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

Using With Existing Clones
--------------------------

Though it's recommended that you allow synchg to perform the initial clone of a
repository, it is possible to use it with existing clones.  You simply need to
make sure that the remote repository is listed as a remote in the .hgrc for
your local repository.  The remote should be named using the hostname of the
remote machine.

If you intend to use mq patches, this will also need to be done with the mq
repository.


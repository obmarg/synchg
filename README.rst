synchg
======

When developing a cross platform application it can be neccesary to transfer
changes between different machines in order to test changes out.  Mercurials
push & pull help to make this process simpler, however keeping your
repositories in sync is not neccesarily a single step process.  Particularly if
you rebase and collapse changesets quite frequently, and especially if you like
to make use of the mq extension.

This script intends to make the process of syncing two mercurial repositories
to exactly the same point as easy as possible, by taking care of all the steps
neccesary in a single command.

Currently it can:

* Clone a new remote repository
* Refresh the local mq patch
* Strip superflous changesets from the remote repository
* Push to and update the remote repository
* Commit to the local mq repository
* Push to and update the remote mq repository
* Ensure the remote repository has the correct mq patches pushed 

Requirements
------------

Python 2.7 & Mercurial 2.3 are recommended, though others may work.

Synchg depends on these python packages:

* `Plumbum <https://github.com/tomerfiliba/plumbum>`_
* `Clint <https://github.com/kennethreitz/clint>`_

It also requires the `mq <http://mercurial.selenic.com/wiki/MqExtension>`_
mercurial extension is enabled on any remote machines it is used with.

Installation
-------------

Synchg and it's python dependencies can be installed via pip::
  
  pip install synchg


Preparing Repositories
-----------------------

Prior to running synchg for the first time it is recommended that you delete
any remote repositories you intend to use it with, and allow synchg to
perform the initial clone.  If you intend to use mq patches with synchg, you
should also ensure you have run ``hg init --mq`` on your local repositories.

It should be noted that synchg regards remote repositories as "slaves" and will
strip out any changesets it finds that are not in the local repository.  You
will be prompted before this happens, but the script will be unable to continue
if you don't answer yes.  This is to avoid creating additional heads on the
remote. 

Usage
-----

Synchg should be run from the command line::

  synchg remote_host [local_path=None]

Where ``remote_host`` is the host you wish to sync with and ``local_path`` is
the optional path to the local mercurial repository (if missing, the current
directory will be assumed)

More options can be found by running::

  synchg --help

On first run, you will be prompted for some configuration options:

* Remote source directory - this is the path on the remote under which all your
  repositories should be found

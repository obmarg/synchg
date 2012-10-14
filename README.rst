synchg
======

When developing a cross platform application, it can be neccesary to transfer
changes between different machines running different operating systems.
Mercurials push & pull help a lot to make this process a lot simpler than it
could be. However the process of syncing repositories can take quite a few
steps if (like me) you rebase and collapse changesets quite frequently, and
especially if you like to make use of the mq extension.

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


Usage
-----

Synchg is intended to be run from the command line::

  synchg remote_host [local_path=None]

Where ``remote_host`` is the host you wish to sync with and ``local_path`` is
the optional path to the local mercurial repository (if missing, the current
directory will be assumed)

More options can be found by running::

  synchg --help

On first run, synchg will prompt you for some configuration options:

* Remote source directory - this is the path on the remote under which all your
  repositories should be found

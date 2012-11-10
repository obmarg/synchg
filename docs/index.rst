.. raw:: html

    <div style="float:right; margin-left:1em; padding: 1em 2em 1em 2em; background-color: #efefef;
        border-radius: 5px; border-width: thin; border-style: dotted; border-color: #0C3762;">
    <strong>Quick Links</strong><br/>
    <ul>
    <li><a href="#installation" title="Jump to install">Installation</a></li>
    <li><a href="#using-synchg" title="Jump to usage info">Usage</a></li>
    <li><a href="#synchg-api" title="Jump to API reference">API Reference</a></li>
    <li><a href='https://github.com/obmarg/synchg'>GitHub</a></li>
    <li><a href='https://github.com/obmarg/synchg/issues'>Issue Tracker</a></li>
    </ul>
    <a href="http://travis-ci.org/obmarg/synchg" target="_blank">
    <img src="https://secure.travis-ci.org/obmarg/synchg.png" 
    style="display: block; margin-left: auto; margin-right: auto;" title="Travis CI status"></a>
    </div>

.. include:: ../README.rst

SyncHg API 
=============

Synchg also exposes a simple python API that can be used to integrate synchg
functionality into other python projects such as build scripts.

The SyncHg API can be used easily, simply by calling the
:func:`synchg.sync.SyncRemote` function.  For example:

.. literalinclude:: examples/apiexample.py

.. synchg.sync:

Syncing Utilities (synchg.sync)
-------------------------------

.. automodule:: synchg.sync
    :members:

.. synchg.repo:

Repository Control (synchg.repo)
--------------------------------

.. automodule:: synchg.repo
    :members:

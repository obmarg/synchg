0.9.5
-----
* Produced proper documentation using sphinx
* No functional changes

0.9.4
-----
* Removed dependency on my putty/plumbum hacks on windows, as the upstream
  issue in plumbum has now been fixed.

0.9.3
-----
* Another pypi fix for importing synchg

0.9.2
-----
* Fixed another issue with pypi installations, they depended on the synchg
  package for getting the version number, but this lead to attempting to import
  plumbum before it was installed.

0.9.1
-----
* Fixed an issue with pypi installations, which depended on
  ``distribute_setup.py``, which is unavaliable from the pypi archive.

0.9.0
-----
Initial release

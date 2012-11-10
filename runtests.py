#!/usr/bin/env python

from plumbum import FG
from plumbum.cmd import nosetests

nosetests['--with-spec', '--spec-color', '-i',
          '^(it|ensure|must|should|specs?|examples?|tests?)'] & FG

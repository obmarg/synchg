
from synchg import SyncRemote

print "Enter the following details:"
host = raw_input('Remote host: ')
repo_name = raw_input('Repository name: ')
local_path = raw_input('Local path: ')
remote_root = raw_input('Remote root: ')

SyncRemote(host, repo_name, local_path, remote_root)

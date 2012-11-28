from mock import Mock, MagicMock, create_autospec, sentinel, call, patch
from mock import DEFAULT, ANY
from should_dsl import should, should_not
from plumbum.local_machine import LocalMachine, Workdir
from plumbum.commands import ProcessExecutionError
from synchg.repo import Repo, RepoConfig

# Keep pep8 happy
equal_to = be = be_called = throw = None


def setUp():
    Repo.Testing = True


def tearDown():
    Repo.Testing = False


def CreateRepo(remote=None, clean_mq=False):
    machine = create_autospec(LocalMachine, instance=True)
    machine.cwd = create_autospec(Workdir, instance=True)
    repo = Repo(machine, remote)
    if not clean_mq:
        # Mock away CleanMq to stop it messing with things
        repo.CleanMq = MagicMock()
    return repo


class TestRepoCleanMq:
    @patch.multiple(
            Repo, lastAppliedPatch=sentinel.patch,
            PopPatch=DEFAULT, PushPatch=DEFAULT
            )
    def should_push_after_done(self, PopPatch, PushPatch):
        repo = CreateRepo(clean_mq=True)
        with repo.CleanMq():
            assert PopPatch.called
            assert not PushPatch.called
        repo.PushPatch.assert_called_with(sentinel.patch)

    @patch.multiple(
            Repo, lastAppliedPatch=None,
            PopPatch=DEFAULT, PushPatch=DEFAULT
            )
    def should_not_push_if_no_patches(self, PopPatch, PushPatch):
        repo = CreateRepo(clean_mq=True)
        with repo.CleanMq():
            assert PopPatch.called
            assert not PushPatch.called
        assert not PushPatch.called


class TestRepoSummary:
    def doTest(self, commitLine, mqLine, expected):
        repo = CreateRepo()
        repo.hg.return_value = '\n'.join([commitLine, mqLine])
        repo.summary |should| equal_to(expected)
        repo.hg.assert_called_with('summary')

    def it_handles_no_data(self):
        self.doTest('', '', ((0, 0), (0, 0)))

    def it_handles_no_unknowns(self):
        self.doTest('commit: 10 modified', '', ((10, 0), (0, 0)))

    def it_handles_modified_and_unknown(self):
        self.doTest('commit: 10 modified, 20 unknown', '', ((10, 20), (0, 0)))

    def it_handles_mq_applied(self):
        self.doTest('', 'mq: 3 applied', ((0, 0), (3, 0)))

    def it_handles_mq_unapplied(self):
        self.doTest('', 'mq: 4 unapplied', ((0, 0), (0, 4)))

    def it_handles_mq_applied_and_unapplied(self):
        self.doTest('', 'mq: 10 applied, 4 unapplied', ((0, 0), (10, 4)))


class TestRepoCurrentRev:
    def it_parses_correct_revision(self):
        repo = CreateRepo()
        repo.hg.return_value = 'abc43256712f 4.7'
        repo.currentRev |should| equal_to('abc43256712f')
        repo.hg.assert_called_with('id', '-i', '-b')


class TestRepoBranch:
    def it_parses_correct_branch(self):
        repo = CreateRepo()
        repo.hg.return_value = 'abc43256712f 4.7'
        repo.branch |should| equal_to('4.7')
        repo.hg.assert_called_with('id', '-i', '-b')


class TestRepoOutgoings:
    def it_requires_remote(self):
        repo = CreateRepo()
        (lambda: repo.outgoings) |should| throw(AssertionError)

    @patch.multiple(Repo, branch=None, currentRev=None)
    def it_parses_changeset_info(self):
        data = '\n\ntsd345678123454\tA nice changeset\n123\tAnother changeset'
        repo = CreateRepo(sentinel.remote)
        repo.hg[''].return_value = data
        repo.outgoings |should| equal_to([
            ('tsd345678123454', 'A nice changeset'),
            ('123', 'Another changeset')
            ])

    @patch.multiple(Repo, branch=None, currentRev=None)
    def it_ignores_empty_list_return_code(self):
        repo = CreateRepo(sentinel.remote)
        repo.hg[''].side_effect = ProcessExecutionError('', 1, '', '')
        repo.outgoings |should| equal_to([])

    @patch.multiple(Repo, branch=None, currentRev=None)
    def should_propagate_other_errors(self):
        repo = CreateRepo(sentinel.remote)
        repo.hg[''].side_effect = ProcessExecutionError('', 2, '', '')
        (lambda: repo.outgoings) |should| throw(ProcessExecutionError)


class TestRepoIncomings:
    def it_requires_remote(self):
        repo = CreateRepo()
        (lambda: repo.incomings) |should| throw(AssertionError)

    @patch.multiple(Repo, branch=None, currentRev=None)
    def it_parses_changeset_info(self):
        data = '\n\ntsd345678123454\tA nice changeset\n123\tAnother changeset'
        repo = CreateRepo(sentinel.remote)
        repo.hg[''].return_value = data
        repo.incomings |should| equal_to([
            ('tsd345678123454', 'A nice changeset'),
            ('123', 'Another changeset')
            ])

    @patch.multiple(Repo, branch=None, currentRev=None)
    def it_ignores_empty_list_return_code(self):
        repo = CreateRepo(sentinel.remote)
        repo.hg[''].side_effect = ProcessExecutionError('', 1, '', '')
        repo.incomings |should| equal_to([])

    @patch.multiple(Repo, branch=None, currentRev=None)
    def should_propagate_other_errors(self):
        repo = CreateRepo(sentinel.remote)
        repo.hg[''].side_effect = ProcessExecutionError('', 2, '', '')
        (lambda: repo.incomings) |should| throw(ProcessExecutionError)


class TestRepoLastAppliedPatch:
    def should_return_none_if_mq_disabled(self):
        repo = CreateRepo()
        repo.hg.side_effect = ProcessExecutionError('', 255, '', '')
        repo.lastAppliedPatch |should| be(None)

    def should_return_none_if_no_patches(self):
        repo = CreateRepo()
        repo.hg.side_effect = ProcessExecutionError('', 1, '', '')
        repo.lastAppliedPatch |should| be(None)

    def should_propagate_other_errors(self):
        repo = CreateRepo()
        repo.hg.side_effect = ProcessExecutionError('', 2, '', '')
        (lambda: repo.lastAppliedPatch) |should| throw(ProcessExecutionError)

    def should_return_a_patch(self):
        repo = CreateRepo()
        repo.hg.return_value = 'something\n\n'
        repo.lastAppliedPatch |should| equal_to('something')


class TestRepoPushToRemote:
    def should_assert_if_no_remote(self):
        repo = CreateRepo()
        repo.PushMqToRemote |should| throw(AssertionError)

    @patch.multiple(
            Repo, branch=sentinel.branch, currentRev=sentinel.currentRev
            )
    def should_push_branch_and_rev(self):
        repo = CreateRepo(sentinel.remote)
        repo.PushToRemote()
        repo.hg.assert_called_with(
                'push', '-b', sentinel.branch, '-r', sentinel.currentRev,
                sentinel.remote
                )


class TestRepoPushMqToRemote:
    def should_assert_if_no_remote(self):
        repo = CreateRepo()
        repo.PushMqToRemote |should| throw(AssertionError)

    def should_push_mq(self):
        repo = CreateRepo(sentinel.remote)
        repo.PushMqToRemote()
        repo.hg.assert_called_with('push', '--mq', sentinel.remote)

    def should_ignore_no_outgoings_return_code(self):
        repo = CreateRepo(sentinel.remote)
        repo.hg.side_effect = ProcessExecutionError('', 1, '', '')
        repo.PushMqToRemote |should_not| throw(ProcessExecutionError)

    def should_propagate_other_errors(self):
        repo = CreateRepo(sentinel.remote)
        repo.hg.side_effect = ProcessExecutionError('', 2, '', '')
        repo.PushMqToRemote |should| throw(ProcessExecutionError)


class TestRepoPopPatch:
    @patch.object(Repo, 'lastAppliedPatch', None)
    def it_only_pops_if_needed(self):
        repo = CreateRepo()
        repo.PopPatch(sentinel.patch)
        repo.PopPatch()
        assert not repo.hg.called

    @patch.object(Repo, 'lastAppliedPatch', True)
    def it_pops_all_by_default(self):
        repo = CreateRepo()
        repo.PopPatch()
        repo.hg.assert_called_with('qpop', '-a')

    @patch.object(Repo, 'lastAppliedPatch', True)
    def it_pops_a_specific_patch_if_requested(self):
        repo = CreateRepo()
        repo.PopPatch(sentinel.patch)
        repo.hg.assert_called_with('qpop', sentinel.patch)


class TestRepoPushPatch:
    def it_pushes_all_by_default(self):
        repo = CreateRepo()
        repo.PushPatch()
        repo.hg.assert_called_with('qpush', '-a')

    def it_pushes_a_specific_patch_if_requested(self):
        repo = CreateRepo()
        repo.PushPatch(sentinel.patch)
        repo.hg.assert_called_with('qpush', sentinel.patch)


class TestRepoStrip:
    def it_strips_some_changesets(self):
        repo = CreateRepo()
        data = [Repo.ChangesetInfo(i, sentinel.desc) for i in range(5)]
        repo.Strip(data)
        repo.hg.assert_called_with('strip', 0, 1, 2, 3, 4)


class TestRepoUpdate:
    def it_accepts_changeset_info(self):
        repo = CreateRepo()
        data = Repo.ChangesetInfo(sentinel.hash, sentinel.desc)
        repo.Update(data)
        repo.hg.assert_called_with('update', sentinel.hash)

    def it_accepts_changeset_hash(self):
        repo = CreateRepo()
        repo.Update(sentinel.hash)
        repo.hg.assert_called_with('update', sentinel.hash)


class TestRepoUpdateMq:
    def it_updates_mq(self):
        repo = CreateRepo()
        repo.UpdateMq()
        repo.hg.assert_called_with('update', '--mq')


class TestRepoRefreshMq:
    def it_refreshes_mq(self):
        repo = CreateRepo()
        repo.RefreshMq()
        repo.hg.assert_called_with('qrefresh')


class TestRepoCommitMq:
    def it_has_a_default_message(self):
        repo = CreateRepo()
        repo.CommitMq()
        repo.hg.assert_called_with('commit', '--mq', '-m', ANY)

    def it_accepts_a_message(self):
        repo = CreateRepo()
        repo.CommitMq(sentinel.message)
        repo.hg.assert_called_with('commit', '--mq', '-m', sentinel.message)

    def it_ignores_no_change_return_code(self):
        repo = CreateRepo()
        repo.hg.side_effect = ProcessExecutionError('', 1, '', '')
        repo.CommitMq()
        assert repo.hg.called

    def it_propagates_other_errors(self):
        repo = CreateRepo()
        repo.hg.side_effect = ProcessExecutionError('', 2, '', '')
        repo.CommitMq |should| throw(ProcessExecutionError)


class TestRepoInitMq:
    def it_runs_init_mq(self):
        repo = CreateRepo()
        repo.InitMq()
        repo.hg.assert_called_with('init', '--mq')


class TestRepoClone:
    @patch.object(Repo, 'config', None)
    def it_clones_main_repo(self):
        repo = CreateRepo()
        (repo._path / '.hg' / 'patches').exists.return_value = False
        repo.Clone(sentinel.destination, False)
        repo.hg.assert_called_with('clone', '.', sentinel.destination)

    @patch.multiple(Repo, config=None, mqconfig=None, CloneMq=DEFAULT)
    def it_clones_mq_repo_if_there(self, CloneMq):
        repo = CreateRepo()
        (repo._path / '.hg' / 'patches').exists.return_value = True
        repo.Clone('machine', False)
        repo.hg.assert_called_with('clone', '.', 'machine')
        CloneMq.assert_called_with('machine', False)

    @patch.multiple(
            Repo,
            config=Mock(spec_set=RepoConfig),
            mqconfig=Mock(spec_set=RepoConfig)
            )
    def it_sets_up_remote(self):
        repo = CreateRepo(sentinel.remote)
        (repo._path / '.hg' / 'patches').exists.return_value = False
        repo.Clone('dest')
        repo.config.AddRemote.assert_called_with(sentinel.remote, 'dest')
        repo.mqconfig.AddRemote |should_not| be_called


class TestMqClone:
    @patch.multiple(Repo, config=None, mqconfig=None)
    def it_clones(self):
        repo = CreateRepo()
        repo.CloneMq('dest', False)
        repo.hg.assert_called_with('clone', '.', 'dest/.hg/patches')

    @patch.multiple(
            Repo, config=Mock(spec_set=RepoConfig),
            mqconfig=Mock(spec_set=RepoConfig)
            )
    def it_sets_up_mq_remote(self):
        repo = CreateRepo(sentinel.remote)
        repo.CloneMq('dest')
        repo.mqconfig.AddRemote.assert_called_with(
                sentinel.remote, 'dest/.hg/patches'
                )
        repo.config.AddRemote |should_not| be_called
        repo.mqconfig.AddRemote |should| be_called


class TestRepoConfig(object):
    @patch('synchg.repo.ConfigParser', autospec=True)
    def it_reads_config_if_there(self, config_parser):
        path = MagicMock()
        (path / '.hg' / 'hgrc').exists.return_value = True
        (path / '.hg' / 'hgrc').open.return_value = sentinel.config
        RepoConfig(path)
        config_parser.assert_has_calls([
                call(),
                call().readfp(sentinel.config)
                ])

    @patch('synchg.repo.ConfigParser', autospec=True)
    def it_creates_paths_section_if_needed(self, config_parser):
        path = MagicMock()
        (path / '.hg' / 'hgrc').exists.return_value = False
        RepoConfig(path)
        config_parser.assert_has_calls([
                call(),
                call().add_section('paths')
                ])

    @patch('synchg.repo.ConfigParser', autospec=True)
    def it_allows_add_remote(self, config_parser):
        path = MagicMock()
        (path / '.hg' / 'hgrc').exists.return_value = False
        (path / '.hg' / 'hgrc').open.return_value = sentinel.config
        config = RepoConfig(path)
        config_parser.reset_mock()
        config.AddRemote(sentinel.remote, sentinel.destination)
        config_parser.assert_has_calls([
                call().set('paths', sentinel.remote, sentinel.destination),
                call().write(sentinel.config)
                ])

    @patch('synchg.repo.ConfigParser', autospec=True)
    def it_returns_remote_dict(self, __):
        config = RepoConfig(MagicMock())
        config._config.reset_mock()
        config._config.items.return_value = [
                ('key1', sentinel.value1),
                ('key2', sentinel.value2)
                ]
        config.remotes |should| equal_to(
                dict(key1=sentinel.value1, key2=sentinel.value2)
                )
        config._config.items.assert_called_with('paths')



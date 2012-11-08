from mock import MagicMock, create_autospec, sentinel, call, patch
from plumbum.local_machine import LocalMachine, Workdir
from synchg.repo import Repo


def CreateRepo(remote=None, clean_mq=False):
    machine = create_autospec(LocalMachine, instance=True)
    machine.cwd = create_autospec(Workdir, instance=True)
    repo = Repo(machine, remote)
    if not clean_mq:
        # Mock away CleanMq to stop it messing with things
        repo.CleanMq = MagicMock()
    return repo


class TestRepoConstructor:
    # TODO: Implement this stuff
    pass


class TestRepoCleanMq:
    def should_push_after_done(self):
        pass

    def should_not_push_if_no_patches(self):
        pass

    def should_allow_recursion(self):
        pass


class TestRepoSummary:
    def it_handles_no_mq(self):
        pass

    def it_handles_no_unknowns(self):
        pass

    def it_handles_modified_and_unknown(self):
        pass

    def it_handles_mq_applied(self):
        pass

    def it_handles_mq_unapplied(self):
        pass

    def it_handles_mq_applied_and_unapplied(self):
        pass


class TestRepoCurrentRev:
    def it_only_checks_once(self):
        pass

    def it_parses_correct_revision(self):
        pass


class TestRepoCurrentBranch:
    def it_only_checks_once(self):
        pass

    def it_parses_correct_branch(self):
        pass


class TestRepoOutgoings:
    def it_ignores_empty_list_return_code(self):
        pass

    def it_parses_changeset_info(self):
        pass


class TestRepoIncomings:
    def it_parses_changeset_info(self):
        pass

    def it_ignores_empty_list_return_code(self):
        pass

    def should_propagate_other_errors(self):
        pass


class TestRepoLastAppliedPatch:
    def should_return_none_if_mq_disabled(self):
        pass

    def should_return_none_if_no_patches(self):
        pass

    def should_return_last_patch_in_list(self):
        pass


class TestRepoPushToRemote:
    def should_push_branch_and_rev(self):
        pass


class TestRepoPushMqToRemote:
    def should_push_mq(self):
        pass

    def should_ignore_no_outgoings_return_code(self):
        pass

    def should_propagate_other_errors(self):
        pass


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
        pass


class TestRepoRefreshMq:
    def it_refreshes_mq(self):
        pass


class TestRepoCommitMq:
    def it_has_a_default_message(self):
        pass

    def it_accepts_a_message(self):
        pass

    def it_ignores_no_change_return_code(self):
        pass

    def it_propagates_other_errors(self):
        pass


class TestRepoClone:
    def it_clones_main_repo(self):
        repo = CreateRepo()
        (repo.machine.cwd / '.hg' / 'patches').exists.return_value = False
        repo.Clone(sentinel.destination, False)
        # TODO: would be nice to use should_dsl for this.
        #       (Probably with should aliased as was or something)
        repo.hg.assert_called_with('clone', '.', sentinel.destination)
        pass

    def it_clones_mq_repo_if_there(self):
        repo = CreateRepo()
        (repo.machine.cwd / '.hg' / 'patches').exists.return_value = True
        repo.Clone('machine', False)
        # TODO: would be nice to use should_dsl for this.
        #       (Probably with should aliased as was or something)
        print repo.hg.mock_calls
        repo.hg.assert_has_calls([
                call('clone', '.', 'machine'),
                call('clone', '.', 'machine' + '/.hg/patches')
                ])

    @patch('synchg.repo.ConfigParser', autospec=True)
    def it_sets_up_remote(self, config_parser):
        repo = CreateRepo(sentinel.remote)
        (repo.machine.cwd / '.hg' / 'patches').exists.return_value = False
        (repo.machine.cwd / '.hg' / 'hgrc').exists.return_value = True
        (repo.machine.cwd / '.hg' / 'hgrc').open.return_value = sentinel.config
        repo.Clone('dest')
        config_parser.assert_has_calls([
                call(),
                call().readfp(sentinel.config),
                call().set('paths', sentinel.remote, 'dest'),
                call().write(sentinel.config)
                ])

    @patch('synchg.repo.ConfigParser', autospec=True)
    def it_creates_hgrc_when_setting_up_remote(self, config_parser):
        repo = CreateRepo(sentinel.remote)
        (repo.machine.cwd / '.hg' / 'patches').exists.return_value = False
        (repo.machine.cwd / '.hg' / 'hgrc').exists.return_value = False
        (repo.machine.cwd / '.hg' / 'hgrc').open.return_value = sentinel.config
        repo.Clone('dest')
        assert not config_parser.readfp.called
        config_parser.assert_has_calls([
                call(),
                call().add_section('paths'),
                call().set('paths', sentinel.remote, 'dest'),
                call().write(sentinel.config)
                ])

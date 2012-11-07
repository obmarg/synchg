import mox


class TestRepoCleanMq(mox.MoxTestBase):
    def should_push_after_done(self):
        pass

    def should_not_push_if_no_patches(self):
        pass

    def should_allow_recursion(self):
        pass


class TestRepoSummary(mox.MoxTestBase):
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


class TestRepoCurrentRev(mox.MoxTestBase):
    def it_only_checks_once(self):
        pass

    def it_parses_correct_revision(self):
        pass


class TestRepoCurrentBranch(mox.MoxTestBase):
    def it_only_checks_once(self):
        pass

    def it_parses_correct_branch(self):
        pass


class TestRepoOutgoings(mox.MoxTestBase):
    def it_ignores_empty_list_return_code(self):
        pass

    def it_parses_changeset_info(self):
        pass


class TestRepoIncomings(mox.MoxTestBase):
    def it_parses_changeset_info(self):
        pass

    def it_ignores_empty_list_return_code(self):
        pass

    def should_propagate_other_errors(self):
        pass


class TestRepoLastAppliedPatch(mox.MoxTestBase):
    def should_return_none_if_mq_disabled(self):
        pass

    def should_return_none_if_no_patches(self):
        pass

    def should_return_last_patch_in_list(self):
        pass


class TestRepoPushToRemote(mox.MoxTestBase):
    def should_push_branch_and_rev(self):
        pass


class TestRepoPushMqToRemote(mox.MoxTestBase):
    def should_push_mq(self):
        pass

    def should_ignore_no_outgoings_return_code(self):
        pass

    def should_propagate_other_errors(self):
        pass


class TestRepoPopPatch(mox.MoxTestBase):
    def it_only_pops_if_needed(self):
        pass

    def it_pops_all_by_default(self):
        pass

    def it_pops_a_specific_patch_if_requested(self):
        pass


class TestRepoPushPatch(mox.MoxTestBase):
    def it_pushes_all_by_default(self):
        pass

    def it_pushes_a_specific_patch_if_requested(self):
        pass


class TestRepoStrip(mox.MoxTestBase):
    def it_strips_some_changesets(self):
        pass


class TestRepoUpdate(mox.MoxTestBase):
    def it_accepts_changeset_info(self):
        pass

    def it_accepts_changeset_hash(self):
        pass


class TestRepoUpdateMq(mox.MoxTestBase):
    def it_updates_mq(self):
        pass


class TestRepoRefreshMq(mox.MoxTestBase):
    def it_refreshes_mq(self):
        pass


class TestRepoCommitMq(mox.MoxTestBase):
    def it_has_a_default_message(self):
        pass

    def it_accepts_a_message(self):
        pass

    def it_ignores_no_change_return_code(self):
        pass

    def it_propagates_other_errors(self):
        pass


class TestRepoClone(mox.MoxTestBase):
    def it_clones_main_repo(self):
        pass

    def it_clones_mq_repo_if_there(self):
        pass

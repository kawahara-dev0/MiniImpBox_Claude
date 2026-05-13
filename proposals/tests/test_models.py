import pytest
from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError

from proposals.models import Proposal, StatusHistory

User = get_user_model()


@pytest.mark.django_db
class TestProposalModel:
    def test_status_choices_values(self):
        expected = {'new', 'reviewing', 'planned', 'done', 'declined'}
        assert Proposal.VALID_STATUSES == expected

    def test_valid_statuses_matches_status_choices(self):
        from_choices = {s[0] for s in Proposal.STATUS_CHOICES}
        assert Proposal.VALID_STATUSES == from_choices

    def test_status_choices_has_five_items(self):
        assert len(Proposal.STATUS_CHOICES) == 5

    def test_status_constants_are_in_valid_statuses(self):
        assert Proposal.STATUS_NEW in Proposal.VALID_STATUSES
        assert Proposal.STATUS_REVIEWING in Proposal.VALID_STATUSES
        assert Proposal.STATUS_PLANNED in Proposal.VALID_STATUSES
        assert Proposal.STATUS_DONE in Proposal.VALID_STATUSES
        assert Proposal.STATUS_DECLINED in Proposal.VALID_STATUSES

    def test_default_status_is_new(self):
        p = Proposal(title='T', body='B')
        assert p.status == Proposal.STATUS_NEW

    def test_submitter_name_default_blank(self):
        p = Proposal(title='T', body='B')
        assert p.submitter_name == ''

    def test_submitter_contact_default_blank(self):
        p = Proposal(title='T', body='B')
        assert p.submitter_contact == ''

    def test_ordering_is_descending_created_at(self):
        assert Proposal._meta.ordering == ['-created_at']

    def test_create_and_retrieve(self):
        p = Proposal.objects.create(title='Hello', body='World')
        assert p.pk is not None
        assert p.status == 'new'
        assert p.created_at is not None
        assert p.updated_at is not None


@pytest.mark.django_db
class TestStatusHistoryModel:
    def _make_proposal(self):
        return Proposal.objects.create(title='T', body='B')

    def _make_user(self, email='admin@example.com'):
        return User.objects.create_user(
            username=email, email=email, password='pass',
            is_staff=True,
        )

    def test_ordering_is_ascending_changed_at(self):
        assert StatusHistory._meta.ordering == ['changed_at']

    def test_create_status_history(self):
        p = self._make_proposal()
        u = self._make_user()
        sh = StatusHistory.objects.create(
            proposal=p,
            changed_by=u,
            old_status='new',
            new_status='reviewing',
        )
        assert sh.pk is not None
        assert sh.changed_at is not None

    def test_protect_on_delete_proposal(self):
        """Deleting a proposal that has a StatusHistory row must raise ProtectedError."""
        p = self._make_proposal()
        u = self._make_user()
        StatusHistory.objects.create(
            proposal=p, changed_by=u, old_status='new', new_status='reviewing',
        )
        with pytest.raises(ProtectedError):
            p.delete()

    def test_protect_on_delete_user(self):
        """Deleting a user referenced in StatusHistory must raise ProtectedError."""
        p = self._make_proposal()
        u = self._make_user()
        StatusHistory.objects.create(
            proposal=p, changed_by=u, old_status='new', new_status='reviewing',
        )
        with pytest.raises(ProtectedError):
            u.delete()

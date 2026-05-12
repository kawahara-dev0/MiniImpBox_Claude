"""
TDD tests for admin proposal views: AdminProposalListView, AdminProposalDetailView,
AdminStatusChangeView.

Step 7 — High-risk: status change atomicity + sensitive data non-disclosure.
TDD required for atomicity and sensitive data per roadmap Step 7.
Tests written before implementation.
"""
import pytest
from django.contrib.auth import get_user_model
from proposals.models import Proposal, StatusHistory

User = get_user_model()

LIST_URL = '/admin-portal/proposals/'
LOGIN_URL = '/admin-portal/login/'


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username='admin@example.com',
        email='admin@example.com',
        password='adminpass',
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def non_staff_user(db):
    return User.objects.create_user(
        username='user@example.com',
        email='user@example.com',
        password='userpass',
        is_staff=False,
        is_active=True,
    )


@pytest.fixture
def proposal(db):
    return Proposal.objects.create(
        title='Test Proposal',
        body='Test body content.',
        submitter_name='Bob',
        submitter_contact='bob@example.com',
    )


# ============================================================
# AdminProposalListView
# ============================================================

class TestAdminProposalListView:

    def test_unauthenticated_redirects_to_login(self, client, db):
        response = client.get(LIST_URL)
        assert response.status_code == 302
        assert response['Location'].startswith(LOGIN_URL)

    def test_non_staff_returns_403(self, client, non_staff_user):
        client.force_login(non_staff_user)
        response = client.get(LIST_URL)
        assert response.status_code == 403

    def test_staff_gets_200(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get(LIST_URL)
        assert response.status_code == 200

    def test_staff_sees_proposals_in_list(self, client, staff_user, proposal):
        client.force_login(staff_user)
        response = client.get(LIST_URL)
        assert proposal.title in response.content.decode()

    def test_list_uses_correct_template(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get(LIST_URL)
        assert 'proposals/admin_list.html' in [t.name for t in response.templates]

    def test_pagination_context_present(self, client, staff_user, db):
        client.force_login(staff_user)
        response = client.get(LIST_URL)
        assert 'page_obj' in response.context


# ============================================================
# AdminProposalDetailView
# ============================================================

class TestAdminProposalDetailView:

    def _detail_url(self, pk):
        return f'/admin-portal/proposals/{pk}/'

    def test_unauthenticated_redirects_to_login(self, client, proposal):
        response = client.get(self._detail_url(proposal.pk))
        assert response.status_code == 302
        assert response['Location'].startswith(LOGIN_URL)

    def test_non_staff_returns_403(self, client, non_staff_user, proposal):
        client.force_login(non_staff_user)
        response = client.get(self._detail_url(proposal.pk))
        assert response.status_code == 403

    def test_staff_gets_200(self, client, staff_user, proposal):
        client.force_login(staff_user)
        response = client.get(self._detail_url(proposal.pk))
        assert response.status_code == 200

    def test_nonexistent_proposal_returns_404(self, client, staff_user, db):
        client.force_login(staff_user)
        response = client.get('/admin-portal/proposals/99999/')
        assert response.status_code == 404

    def test_detail_uses_correct_template(self, client, staff_user, proposal):
        client.force_login(staff_user)
        response = client.get(self._detail_url(proposal.pk))
        assert 'proposals/admin_detail.html' in [t.name for t in response.templates]

    def test_detail_context_contains_proposal(self, client, staff_user, proposal):
        client.force_login(staff_user)
        response = client.get(self._detail_url(proposal.pk))
        assert response.context['proposal'] == proposal

    def test_detail_context_contains_status_history(self, client, staff_user, proposal):
        client.force_login(staff_user)
        response = client.get(self._detail_url(proposal.pk))
        assert 'history' in response.context

    def test_detail_context_contains_form(self, client, staff_user, proposal):
        client.force_login(staff_user)
        response = client.get(self._detail_url(proposal.pk))
        assert 'form' in response.context


# ============================================================
# AdminStatusChangeView — TDD (atomicity + sensitive data)
# ============================================================

class TestAdminStatusChangeView:

    def _status_url(self, pk):
        return f'/admin-portal/proposals/{pk}/status/'

    def _detail_url(self, pk):
        return f'/admin-portal/proposals/{pk}/'

    def test_unauthenticated_redirects_to_login(self, client, proposal):
        response = client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        assert response.status_code == 302
        assert response['Location'].startswith(LOGIN_URL)

    def test_non_staff_returns_403(self, client, non_staff_user, proposal):
        client.force_login(non_staff_user)
        response = client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        assert response.status_code == 403

    def test_valid_status_change_updates_proposal(self, client, staff_user, proposal):
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        proposal.refresh_from_db()
        assert proposal.status == 'reviewing'

    def test_valid_status_change_creates_history_row(self, client, staff_user, proposal):
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        assert StatusHistory.objects.filter(proposal=proposal).count() == 1

    def test_valid_status_change_history_records_old_and_new_status(self, client, staff_user, proposal):
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        history = StatusHistory.objects.get(proposal=proposal)
        assert history.old_status == 'new'
        assert history.new_status == 'reviewing'

    def test_valid_status_change_history_records_changed_by(self, client, staff_user, proposal):
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        history = StatusHistory.objects.get(proposal=proposal)
        assert history.changed_by == staff_user

    def test_valid_status_change_redirects_to_detail(self, client, staff_user, proposal):
        client.force_login(staff_user)
        response = client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        assert response.status_code == 302
        assert response['Location'] == self._detail_url(proposal.pk)

    # --- Atomicity tests (TDD required) ---

    def test_both_proposal_and_history_updated_atomically(self, client, staff_user, proposal):
        """After valid status change, both proposal.status and StatusHistory exist."""
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'planned'})
        proposal.refresh_from_db()
        assert proposal.status == 'planned'
        assert StatusHistory.objects.filter(proposal=proposal, new_status='planned').exists()

    def test_invalid_status_does_not_update_proposal(self, client, staff_user, proposal):
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'nonexistent_status'})
        proposal.refresh_from_db()
        assert proposal.status == 'new'

    def test_invalid_status_does_not_create_history_row(self, client, staff_user, proposal):
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'nonexistent_status'})
        assert StatusHistory.objects.filter(proposal=proposal).count() == 0

    # --- Sensitive data non-disclosure tests (TDD required) ---

    def test_status_history_has_no_body_field(self, db):
        """StatusHistory model must not have a body column."""
        field_names = [f.name for f in StatusHistory._meta.get_fields()]
        assert 'body' not in field_names

    def test_status_history_has_no_submitter_name_field(self, db):
        field_names = [f.name for f in StatusHistory._meta.get_fields()]
        assert 'submitter_name' not in field_names

    def test_status_history_has_no_submitter_contact_field(self, db):
        field_names = [f.name for f in StatusHistory._meta.get_fields()]
        assert 'submitter_contact' not in field_names

    def test_status_history_row_does_not_contain_proposal_body(self, client, staff_user, proposal):
        """After status change, StatusHistory row contains only expected fields."""
        client.force_login(staff_user)
        client.post(self._status_url(proposal.pk), data={'new_status': 'reviewing'})
        history = StatusHistory.objects.get(proposal=proposal)
        assert not hasattr(history, 'body')
        assert not hasattr(history, 'submitter_name')
        assert not hasattr(history, 'submitter_contact')
        assert history.old_status == 'new'
        assert history.new_status == 'reviewing'

    def test_nonexistent_proposal_status_change_returns_404(self, client, staff_user, db):
        client.force_login(staff_user)
        response = client.post('/admin-portal/proposals/99999/status/', data={'new_status': 'reviewing'})
        assert response.status_code == 404

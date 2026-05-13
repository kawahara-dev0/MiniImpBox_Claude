"""
Tests for public proposal views: ProposalSubmitView, ProposalSubmitCompleteView.

Step 6: Public proposal submission.
Risk: Medium.
"""
from proposals.models import Proposal

SUBMIT_URL = '/'
COMPLETE_URL = '/submit/complete/'


class TestProposalSubmitViewGet:

    def test_get_returns_200(self, client, db):
        response = client.get(SUBMIT_URL)
        assert response.status_code == 200

    def test_get_renders_submit_template(self, client, db):
        response = client.get(SUBMIT_URL)
        assert 'proposals/submit.html' in [t.name for t in response.templates]

    def test_get_contains_form(self, client, db):
        response = client.get(SUBMIT_URL)
        assert 'form' in response.context

    def test_get_contains_csrf_token(self, client, db):
        response = client.get(SUBMIT_URL)
        assert b'csrfmiddlewaretoken' in response.content


class TestProposalSubmitViewPost:

    def test_valid_post_creates_proposal(self, client, db):
        client.post(SUBMIT_URL, data={
            'title': 'Improve break room',
            'body': 'Add a coffee machine.',
        })
        assert Proposal.objects.count() == 1

    def test_valid_post_proposal_has_status_new(self, client, db):
        client.post(SUBMIT_URL, data={
            'title': 'Improve break room',
            'body': 'Add a coffee machine.',
        })
        proposal = Proposal.objects.first()
        assert proposal.status == 'new'

    def test_valid_post_all_fields_saved(self, client, db):
        client.post(SUBMIT_URL, data={
            'title': 'Improve break room',
            'body': 'Add a coffee machine.',
            'submitter_name': 'Alice',
            'submitter_contact': 'alice@example.com',
        })
        proposal = Proposal.objects.first()
        assert proposal.title == 'Improve break room'
        assert proposal.submitter_name == 'Alice'
        assert proposal.submitter_contact == 'alice@example.com'

    def test_valid_post_redirects_to_complete(self, client, db):
        response = client.post(SUBMIT_URL, data={
            'title': 'Improve break room',
            'body': 'Add a coffee machine.',
        })
        assert response.status_code == 302
        assert response['Location'] == COMPLETE_URL

    def test_invalid_empty_title_returns_200(self, client, db):
        response = client.post(SUBMIT_URL, data={
            'title': '',
            'body': 'Some body.',
        })
        assert response.status_code == 200
        assert Proposal.objects.count() == 0

    def test_invalid_empty_body_returns_200(self, client, db):
        response = client.post(SUBMIT_URL, data={
            'title': 'A title',
            'body': '',
        })
        assert response.status_code == 200
        assert Proposal.objects.count() == 0

    def test_invalid_title_too_long_returns_200(self, client, db):
        response = client.post(SUBMIT_URL, data={
            'title': 'x' * 101,
            'body': 'Some body.',
        })
        assert response.status_code == 200
        assert Proposal.objects.count() == 0

    def test_invalid_body_too_long_returns_200(self, client, db):
        response = client.post(SUBMIT_URL, data={
            'title': 'A title',
            'body': 'x' * 2001,
        })
        assert response.status_code == 200
        assert Proposal.objects.count() == 0

    def test_invalid_submitter_contact_returns_200_with_error(self, client, db):
        response = client.post(SUBMIT_URL, data={
            'title': 'A title',
            'body': 'Some body.',
            'submitter_contact': 'not-an-email',
        })
        assert response.status_code == 200
        assert Proposal.objects.count() == 0
        assert 'form' in response.context
        assert response.context['form'].errors


class TestProposalSubmitCompleteView:

    def test_get_returns_200(self, client, db):
        response = client.get(COMPLETE_URL)
        assert response.status_code == 200

    def test_get_renders_complete_template(self, client, db):
        response = client.get(COMPLETE_URL)
        assert 'proposals/submit_complete.html' in [t.name for t in response.templates]

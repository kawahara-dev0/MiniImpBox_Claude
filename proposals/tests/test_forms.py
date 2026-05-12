"""
Tests for ProposalForm.

Step 6: Public proposal submission.
Risk: Medium.
"""
from proposals.forms import ProposalForm


class TestProposalForm:

    def test_valid_all_fields(self, db):
        form = ProposalForm(data={
            'title': 'Improve break room',
            'body': 'Add a coffee machine.',
            'submitter_name': 'Alice',
            'submitter_contact': 'alice@example.com',
        })
        assert form.is_valid(), form.errors

    def test_valid_required_fields_only(self, db):
        form = ProposalForm(data={
            'title': 'Improve break room',
            'body': 'Add a coffee machine.',
            'submitter_name': '',
            'submitter_contact': '',
        })
        assert form.is_valid(), form.errors

    def test_title_required(self, db):
        form = ProposalForm(data={
            'title': '',
            'body': 'Some body text.',
        })
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_body_required(self, db):
        form = ProposalForm(data={
            'title': 'A title',
            'body': '',
        })
        assert not form.is_valid()
        assert 'body' in form.errors

    def test_title_max_length(self, db):
        form = ProposalForm(data={
            'title': 'x' * 101,
            'body': 'Some body.',
        })
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_title_exactly_100_chars_is_valid(self, db):
        form = ProposalForm(data={
            'title': 'x' * 100,
            'body': 'Some body.',
        })
        assert form.is_valid(), form.errors

    def test_body_max_length(self, db):
        form = ProposalForm(data={
            'title': 'A title',
            'body': 'x' * 2001,
        })
        assert not form.is_valid()
        assert 'body' in form.errors

    def test_body_exactly_2000_chars_is_valid(self, db):
        form = ProposalForm(data={
            'title': 'A title',
            'body': 'x' * 2000,
        })
        assert form.is_valid(), form.errors

    def test_submitter_contact_invalid_email_format(self, db):
        form = ProposalForm(data={
            'title': 'A title',
            'body': 'Some body.',
            'submitter_contact': 'not-an-email',
        })
        assert not form.is_valid()
        assert 'submitter_contact' in form.errors

    def test_submitter_contact_valid_email(self, db):
        form = ProposalForm(data={
            'title': 'A title',
            'body': 'Some body.',
            'submitter_contact': 'user@example.com',
        })
        assert form.is_valid(), form.errors

    def test_submitter_contact_empty_is_valid(self, db):
        form = ProposalForm(data={
            'title': 'A title',
            'body': 'Some body.',
            'submitter_contact': '',
        })
        assert form.is_valid(), form.errors

    def test_valid_form_saves_with_status_new(self, db):
        form = ProposalForm(data={
            'title': 'Improve break room',
            'body': 'Add a coffee machine.',
        })
        assert form.is_valid()
        proposal = form.save()
        assert proposal.status == 'new'
        assert proposal.pk is not None

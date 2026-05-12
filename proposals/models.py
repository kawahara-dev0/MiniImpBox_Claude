from django.conf import settings
from django.db import models


class Proposal(models.Model):
    STATUS_NEW       = 'new'
    STATUS_REVIEWING = 'reviewing'
    STATUS_PLANNED   = 'planned'
    STATUS_DONE      = 'done'
    STATUS_DECLINED  = 'declined'

    STATUS_CHOICES = [
        (STATUS_NEW,       'New'),
        (STATUS_REVIEWING, 'Reviewing'),
        (STATUS_PLANNED,   'Planned'),
        (STATUS_DONE,      'Done'),
        (STATUS_DECLINED,  'Declined'),
    ]
    VALID_STATUSES = {s[0] for s in STATUS_CHOICES}

    title             = models.CharField(max_length=100)
    body              = models.TextField()
    submitter_name    = models.CharField(max_length=100, blank=True, default='')
    submitter_contact = models.CharField(max_length=254, blank=True, default='')
    status            = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class StatusHistory(models.Model):
    proposal   = models.ForeignKey(
        Proposal,
        on_delete=models.PROTECT,
        related_name='status_history',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='status_changes',
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['changed_at']

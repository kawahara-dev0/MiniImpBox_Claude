"""
Admin portal proposal URL patterns.

Step 1 placeholder — list stub added in Step 4 to support login redirect.
Real patterns (list, detail, status_change) added in Step 7.
"""
from django.http import HttpResponse
from django.urls import path

app_name = 'proposals_admin'


def _stub_list(request):
    """Temporary stub — replaced by AdminProposalListView in Step 7."""
    return HttpResponse('Admin list placeholder', status=200)


urlpatterns = [
    path('', _stub_list, name='list'),
]

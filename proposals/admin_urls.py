"""
Admin portal proposal URL patterns.

Step 1 placeholder — stub added in Step 4, @admin_required applied in Step 5.
Real views added in Step 7; stub removed.
"""
from django.urls import path

from . import views

app_name = 'proposals_admin'

urlpatterns = [
    path('', views.AdminProposalListView.as_view(), name='list'),
    path('<int:pk>/', views.AdminProposalDetailView.as_view(), name='detail'),
    path('<int:pk>/status/', views.AdminStatusChangeView.as_view(), name='status_change'),
]

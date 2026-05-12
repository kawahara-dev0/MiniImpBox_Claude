"""
URL configuration for Mini Improvement Box v1.

Basic design Section 4.1:
  - proposals.urls     → public proposal routes (/)
  - accounts.urls      → admin portal auth routes (/admin-portal/login|logout/)
  - proposals.admin_urls → admin portal proposal routes (/admin-portal/proposals/)

django.contrib.admin is intentionally omitted (basic design Section 2).
"""
from django.urls import include, path

urlpatterns = [
    path('', include('proposals.urls', namespace='proposals')),
    path('admin-portal/', include('accounts.urls', namespace='accounts')),
    path('admin-portal/proposals/', include('proposals.admin_urls', namespace='proposals_admin')),
]

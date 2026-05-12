from django.urls import path

from . import views

app_name = 'proposals'

urlpatterns = [
    path('', views.ProposalSubmitView.as_view(), name='submit'),
    path('submit/complete/', views.ProposalSubmitCompleteView.as_view(), name='submit_complete'),
]

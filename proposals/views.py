from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.decorators import AdminRequiredMixin
from .forms import ProposalForm, StatusChangeForm
from .models import Proposal, StatusHistory


class ProposalSubmitView(View):
    template_name = 'proposals/submit.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ProposalForm()})

    def post(self, request):
        form = ProposalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('proposals:submit_complete')
        return render(request, self.template_name, {'form': form})


class ProposalSubmitCompleteView(View):
    template_name = 'proposals/submit_complete.html'

    def get(self, request):
        return render(request, self.template_name)


class AdminProposalListView(AdminRequiredMixin, View):
    template_name = 'proposals/admin_list.html'

    def get(self, request):
        qs = Proposal.objects.all()
        paginator = Paginator(qs, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        return render(request, self.template_name, {'page_obj': page_obj})


class AdminProposalDetailView(AdminRequiredMixin, View):
    template_name = 'proposals/admin_detail.html'

    def get(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk)
        history = proposal.status_history.all()
        form = StatusChangeForm()
        error = request.GET.get('error')
        return render(request, self.template_name, {
            'proposal': proposal,
            'history': history,
            'form': form,
            'error': error,
        })


class AdminStatusChangeView(AdminRequiredMixin, View):

    def post(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk)
        form = StatusChangeForm(request.POST)
        if not form.is_valid():
            return redirect(f'/admin-portal/proposals/{pk}/?error=invalid_status')
        new_status = form.cleaned_data['new_status']
        with transaction.atomic():
            old_status = proposal.status
            proposal.status = new_status
            proposal.save(update_fields=['status', 'updated_at'])
            StatusHistory.objects.create(
                proposal=proposal,
                changed_by=request.user,
                old_status=old_status,
                new_status=new_status,
            )
        return redirect('proposals_admin:detail', pk=pk)

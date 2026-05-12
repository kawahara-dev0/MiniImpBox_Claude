from django.shortcuts import redirect, render
from django.views import View

from .forms import ProposalForm


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

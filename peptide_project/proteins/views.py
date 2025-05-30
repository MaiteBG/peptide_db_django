from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from catalog.models import Organism
from proteins.models import Protein


# Create your views here.

class ProteinsByOrganismView(ListView):
    model = Protein
    template_name = "proteins/proteins_by_organism.html"
    context_object_name = "proteins"

    def get_queryset(self):
        scientific_name = self.kwargs["scientific_name"].replace("-", " ")
        return Protein.objects.filter(sequence__organism__scientific_name__iexact=f"{scientific_name}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scientific_name = self.kwargs["scientific_name"].replace("-", " ")
        organism = get_object_or_404(Organism, scientific_name__iexact=scientific_name)
        context["organism"] = organism
        return context

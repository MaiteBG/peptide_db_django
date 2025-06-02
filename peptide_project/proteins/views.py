from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.generic import ListView

from catalog.models import Organism
from proteins.models import Protein


class ProteinsByOrganismView(ListView):
    model = Protein
    template_name = "proteins/proteins_by_organism.html"  # o el path correcto
    context_object_name = "proteins"


    def get_queryset(self):
        slug = self.kwargs["scientific_name"]
        scientific_name = slug.replace("-", " ")
        organism = get_object_or_404(Organism, scientific_name__iexact=scientific_name)
        return Protein.objects.filter(organism=organism)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scientific_name = self.kwargs["scientific_name"].replace("-", " ")
        organism = get_object_or_404(Organism, scientific_name__iexact=scientific_name)
        context["organism"] = organism
        return context

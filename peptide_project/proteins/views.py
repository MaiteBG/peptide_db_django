from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from catalog.models import Organism
from proteins.models import Protein


class ProteinsByOrganismView(ListView):
    model = Protein
    template_name = "proteins/proteins_by_organism.html"
    context_object_name = "proteins"

    def get_queryset(self):
        slug = self.kwargs["scientific_name"]
        scientific_name = slug.replace("-", " ")
        organism = get_object_or_404(Organism, scientific_name__iexact=scientific_name)
        proteins = Protein.objects.filter(organism=organism).select_related('organism', 'sequence')

        # Añadimos atributos extra para las referencias
        for protein in proteins:
            refs = protein.sequence.references.all()
            refs_text = "\n".join(str(ref) for ref in refs)
            protein.references_text = refs_text
            protein.references_text_trunc = (refs_text[:50] + "…") if len(refs_text) > 50 else refs_text

        return proteins

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scientific_name = self.kwargs["scientific_name"].replace("-", " ")
        organism = get_object_or_404(Organism, scientific_name__iexact=scientific_name)
        context["organism"] = organism
        return context

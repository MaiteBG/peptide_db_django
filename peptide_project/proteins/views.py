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

        for protein in proteins:
            refs = protein.sequence.references.all()[1:]
            if refs:
                first = refs[0].__format__("html")
            else:
                first = "N/A"
            # Referencias completas con HTML (por ejemplo, enlaces UniProt)
            rest = "<ul>" + "".join(f"<li>{ref.__format__('html')}</li>" for ref in refs[1:]) + "</ul>" \
                if len(refs) > 1 else ""

            protein.references_text = first + rest

            # Truncado: mostrar siempre la primera línea, y luego añadir puntos suspensivos si hay más
            protein.references_text_trunc = first if len(refs) <= 1 else first + "…"

        return proteins

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scientific_name = self.kwargs["scientific_name"].replace("-", " ")
        organism = get_object_or_404(Organism, scientific_name__iexact=scientific_name)
        context["organism"] = organism
        return context

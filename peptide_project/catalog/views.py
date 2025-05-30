from django.shortcuts import render

# views.py
from django.views.generic import ListView
from catalog.models import Organism


class OrganismListView(ListView):
    model = Organism
    template_name = "catalog/organism_list.html"
    context_object_name = "organisms"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Añadimos los help_text al contexto
        context['help_texts'] = {
            'kingdom': Organism._meta.get_field('kingdom').help_text,
            'phylum': Organism._meta.get_field('phylum').help_text,
            'class_name': Organism._meta.get_field('class_name').help_text,
        }
        return context

from django.shortcuts import render

# views.py
from django.views.generic import ListView
from catalog.models import Organism


class OrganismListView(ListView):
    model = Organism
    template_name = "catalog/organism_list.html"
    context_object_name = "organisms"

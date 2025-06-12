# catalog/views.py
from django.db.models import Count, Q
from django.shortcuts import render
from django.views.generic import ListView
from catalog.models import Organism
import json


class OrganismListView(ListView):
    model = Organism
    template_name = "catalog/organism_list.html"
    context_object_name = "organisms"
    paginate_by = 20  # Añadir paginación

    def get_queryset(self):
        qs = super().get_queryset()

        # Obtener parámetros de filtro
        self.query = self.request.GET.get("query", "")
        self.kingdom = self.request.GET.get('kingdom')
        self.phylum = self.request.GET.get('phylum')
        self.class_name = self.request.GET.get('class_name')

        # Aplicar búsqueda si hay query
        if self.query:
            qs = qs.filter(
                Q(scientific_name__icontains=self.query) |
                Q(common_name__icontains=self.query) |
                Q(kingdom__icontains=self.query) |
                Q(phylum__icontains=self.query) |
                Q(class_name__icontains=self.query)
            )

        # Aplicar filtros jerárquicos
        if self.kingdom:
            qs = qs.filter(kingdom=self.kingdom)
        if self.phylum:
            qs = qs.filter(phylum=self.phylum)
        if self.class_name:
            qs = qs.filter(class_name=self.class_name)

        return qs.order_by('scientific_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener el queryset base (sin paginación)
        base_qs = self.get_queryset().order_by('scientific_name')

        # Kingdoms - siempre todos
        kingdoms = Organism.objects.values('kingdom').annotate(
            count=Count('scientific_name')
        ).order_by('kingdom')

        # Phyla - dependiendo de si hay kingdom seleccionado
        phyla_qs = base_qs
        if self.kingdom:
            phyla_qs = phyla_qs.filter(kingdom=self.kingdom)
        phyla = phyla_qs.values('phylum').annotate(
            count=Count('scientific_name')
        ).order_by('phylum')

        # Classes - dependiendo de kingdom y phylum
        classes_qs = base_qs
        if self.kingdom:
            classes_qs = classes_qs.filter(kingdom=self.kingdom)
        if self.phylum:
            classes_qs = classes_qs.filter(phylum=self.phylum)
        classes = classes_qs.values('class_name').annotate(
            count=Count('scientific_name')
        ).order_by('class_name')

        # Preparar datos para JSON
        def prepare_data(items, field):
            return [
                {"value": item[field], "label": f"{item[field]}", "count": item['count']}
                for item in items if item[field]
            ]

        context.update({
            'kingdoms_json': json.dumps(prepare_data(kingdoms, 'kingdom')),
            'phyla_json': json.dumps(prepare_data(phyla, 'phylum')),
            'classes_json': json.dumps(prepare_data(classes, 'class_name')),
            'selected_kingdom': self.kingdom or '',
            'selected_phylum': self.phylum or '',
            'selected_class_name': self.class_name or '',
            'query': self.query or '',
        })
        print(context["kingdoms_json"])

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'catalog/organism_results.html', context)
        return super().render_to_response(context, **response_kwargs)

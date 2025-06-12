# catalog/views.py

from django.db.models import Count, Q
from django.shortcuts import render
from django.views.generic import ListView
from catalog.models import Organism
import json


def valid_taxonomy(subcategory_value, subcategory_label, supercategory_value, supercategory_label):
    """
    Validates that a subcategory value (e.g., 'phylum' or 'class_name') is consistent
    with a given supercategory value (e.g., 'kingdom' or 'phylum').

    If the value is not among the allowed values for the given supercategory, returns None.

    Args:
        subcategory_value (str): The value of the subcategory to validate.
        subcategory_label (str): The name of the subcategory field (e.g., 'phylum').
        supercategory_value (str): The selected value of the supercategory.
        supercategory_label (str): The name of the supercategory field (e.g., 'kingdom').

    Returns:
        str or None: The validated subcategory value, or None if invalid.
    """
    if supercategory_value:
        allowed_taxs = Organism.objects.values(subcategory_label).filter(
            **{supercategory_label: supercategory_value}
        )
        if subcategory_value not in [item[subcategory_label] for item in allowed_taxs]:
            return None
    return subcategory_value


class OrganismListView(ListView):
    """
    Displays a list of organisms with filtering capabilities based on taxonomy:
    kingdom, phylum, and class_name. Includes dynamic filtering support for HTMX.
    """
    model = Organism
    template_name = "catalog/organism_list.html"
    context_object_name = "organisms"
    paginate_by = 20  # Enable pagination

    def get_queryset(self):
        """
        Builds the filtered queryset based on the GET parameters:
        - query (text search)
        - kingdom
        - phylum
        - class_name

        Applies hierarchical validation between kingdom → phylum and phylum → class_name.
        """
        qs = super().get_queryset()

        # Retrieve filter parameters from the request
        self.query = self.request.GET.get("query", "")
        self.kingdom = self.request.GET.get('kingdom')
        self.phylum = self.request.GET.get('phylum')
        self.class_name = self.request.GET.get('class_name')

        # Validate hierarchical taxonomy consistency
        self.phylum = valid_taxonomy(self.phylum, 'phylum', self.kingdom, 'kingdom')
        self.class_name = valid_taxonomy(self.class_name, 'class_name', self.kingdom, 'kingdom')
        self.class_name = valid_taxonomy(self.class_name, 'class_name', self.phylum, 'phylum')

        # Apply search filtering
        if self.query:
            qs = qs.filter(
                Q(scientific_name__icontains=self.query) |
                Q(common_name__icontains=self.query) |
                Q(kingdom__icontains=self.query) |
                Q(phylum__icontains=self.query) |
                Q(class_name__icontains=self.query)
            )

        # Apply taxonomy filters
        if self.kingdom:
            qs = qs.filter(kingdom=self.kingdom)
        if self.phylum:
            qs = qs.filter(phylum=self.phylum)
        if self.class_name:
            qs = qs.filter(class_name=self.class_name)

        return qs.order_by('scientific_name')

    def get_context_data(self, **kwargs):
        """
        Enriches the context with:
        - Filter options for each taxonomy level (kingdom, phylum, class_name)
        - Current selections
        - Filter options as JSON (for JavaScript rendering)
        """
        context = super().get_context_data(**kwargs)

        # Base queryset to count available values
        base_qs = Organism.objects.order_by('scientific_name')

        # Annotate counts for each filter category
        kingdoms = base_qs.values('kingdom').annotate(
            count=Count('scientific_name')
        ).order_by('kingdom')

        phylums = base_qs.values('phylum').annotate(
            count=Count('scientific_name')
        ).order_by('phylum')

        classes = base_qs.values('class_name').annotate(
            count=Count('scientific_name')
        ).order_by('class_name')

        # Filter subcategories based on selections
        if self.kingdom:
            phylums = phylums.filter(kingdom=self.kingdom)
            classes = classes.filter(kingdom=self.kingdom)

        if self.phylum:
            classes = classes.filter(phylum=self.phylum)

        # Helper to structure data for JSON serialization
        def prepare_data(items, field):
            return [
                {"value": item[field], "label": f"{item[field]}", "count": item['count']}
                for item in items if item[field]
            ]

        # Inject variables into context
        context.update({
            'kingdoms_json': json.dumps(prepare_data(kingdoms, 'kingdom')),
            'phyla_json': json.dumps(prepare_data(phylums, 'phylum')),
            'classes_json': json.dumps(prepare_data(classes, 'class_name')),
            'selected_kingdom': self.kingdom or '',
            'selected_phylum': self.phylum or '',
            'selected_class': self.class_name or '',
            'query': self.query or '',
        })

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a partial or full response depending on whether the request is
        made via HTMX (for dynamic updates) or not.
        """
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'catalog/organism_results.html', context)
        return super().render_to_response(context, **response_kwargs)

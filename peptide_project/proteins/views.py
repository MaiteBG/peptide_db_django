from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q, Case, When, Value, IntegerField
from django.shortcuts import render

from catalog.models import Organism
from proteins.models import Protein


def protein_list(request):
    query = request.GET.get("query", "")
    organism_name = request.GET.get("organism")
    proteins = Protein.objects.select_related("organism", "sequence").all()

    if query:
        proteins = proteins.filter(
            Q(protein_name__icontains=query) | Q(uniprot_code__icontains=query)
        )

    if organism_name:
        proteins = proteins.filter(organism__scientific_name=organism_name)
    paginator = Paginator(proteins, 20)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    # Añadir atributos solo a las proteínas de esta página
    for protein in page_obj:
        refs = protein.sequence.references.annotate(
            priority=Case(
                When(database='UniProt Swiss-Prot', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('priority', 'database', 'db_accession')
        if refs:
            first = refs[0].__format__("html")
        else:
            first = "N/A"

        rest = (
            "<ul>" + "".join(f"<li>{ref.__format__('html')}</li>" for ref in refs[1:]) + "</ul>"
            if len(refs) > 1 else ""
        )

        protein.references_text = first + rest
        protein.references_text_trunc = first if len(refs) <= 1 else first

    organisms = Organism.objects.annotate(protein_count=Count('protein'))
    selected_organism = request.GET.get('organism', '')

    context = {
        "page_obj": page_obj,
        "query": query,
        "organisms": organisms,
        'selected_organism': selected_organism,
    }

    if getattr(request, "htmx", False):
        return render(request, "proteins/protein_list_page.html", context)

    return render(request, "proteins/protein_list.html", context)

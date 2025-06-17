from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q, Case, When, Value, IntegerField
from django.shortcuts import render, redirect
from django.views import View

from catalog.models import Organism
from proteins.models import Protein
from proteins.services import get_proteins_from_organism, get_protein_metadata, create_proteins_from_metadata


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


class ProteinForm:
    pass


class AddProteinView(View):
    template_name = "proteins/add_proteins_from_organism.html"

    def get(self, request):
        organisms = Organism.objects.order_by("scientific_name")
        return render(request, self.template_name, {"organisms": organisms})

    def post(self, request):
        action = request.POST.get("action")
        context_messages = []

        if action == "add_organism":
            sci_name = request.POST.get("new_organism_scientific_name", "").strip()

            if not sci_name:
                context_messages.append("Scientific name cannot be empty.")
            else:
                formatted_name = sci_name.lower().capitalize()

                try:
                    organism, created = Organism.get_or_create_organism(scientific_name=formatted_name)
                    if created:
                        context_messages.append(f"Organism '{formatted_name}' has been successfully added.")
                    else:
                        context_messages.append(
                            f"Organism '{formatted_name}' already exists: {organism.__format__('all')}")
                except Exception as e:
                    context_messages.append(f"An error occurred while adding the organism: {str(e)}")



        elif action == "add_protein":
            # Aquí procesas el formulario proteína
            sci_name = request.POST.get("existing_organism_scientific_name")
            organism, _ = Organism.get_or_create_organism(scientific_name=sci_name)
            proteins = get_proteins_from_organism(organism)
            proteins_meta = get_protein_metadata(proteins)
            created_proteins = create_proteins_from_metadata(proteins_meta, organism)
            # ...

            return redirect("protein-list")

        # Store Django messages for the frontend (if using Django messages framework)
        for msg in context_messages:
            messages.info(request, msg)

        organisms = Organism.objects.all()
        return render(request, self.template_name, {"organisms": organisms})


import uuid
from django.shortcuts import render
from django.http import JsonResponse
from .services import long_task_with_progress


def test_progress_page(request):
    return render(request, "proteins/progress_test.html")


# Vista para lanzar la tarea
def start_task(request):
    task_id = str(uuid.uuid4())
    long_task_with_progress.delay(task_id)
    return JsonResponse({"task_id": task_id})


from django.core.cache import cache
from django.http import JsonResponse


# Vista para consultar progreso
def get_progress(request, task_id):
    print("get progees...")
    progress = cache.get(task_id, "Not started")
    return JsonResponse({"progress": progress})

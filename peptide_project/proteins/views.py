from celery import shared_task
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q, Case, When, Value, IntegerField
from django.views import View

from catalog.models import Organism
from proteins.models import Protein
from proteins.services import get_proteins_from_organism, get_protein_metadata, create_proteins_from_metadata

from django.core.cache import cache
from django.http import JsonResponse


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


class AddProteinView(View):
    template_name = "proteins/add_proteins_from_organism.html"
    partial_template_name = "shared/_task_progress.html"

    def get(self, request):
        organisms = Organism.objects.order_by("scientific_name")
        return render(request, self.template_name, {"organisms": organisms})

    def post(self, request):
        organisms = Organism.objects.order_by("scientific_name")
        action = request.POST.get("action")
        context = {
            "organisms": organisms,
        }

        if action == "add_organism":
            sci_name = request.POST.get("new_organism_scientific_name", "").strip()
            if not sci_name:
                messages.error(request, "Scientific name cannot be empty.")
            else:
                formatted_name = sci_name.lower().capitalize()
                try:
                    organism, created = Organism.get_or_create_organism(scientific_name=formatted_name)
                    if created:
                        messages.success(request,f"Organism {formatted_name} has been successfully added.")
                    else:
                        messages.warning(request,
                            f"Organism '{formatted_name}' already exists")
                    messages.info(request,
                                     f"{organism.__format__('all')}")
                except Exception as e:
                    messages.error(request, f"An error occurred while adding the organism: {str(e)}")

        elif action == "add_protein":
            sci_name = request.POST.get("existing_organism_scientific_name", "").strip()
            if not sci_name:
                messages.error(request, "Please select or enter a scientific name.")
            else:
                # Lanzar tarea sólo si hay sci_name válido
                task_id = str(uuid.uuid4())
                task_add_proteins.delay(sci_name, task_id)

                context["selected_organism"] = sci_name
                context["task_id"] = task_id

        # Si es petición HTMX, devolver solo el fragmento parcial
        if request.headers.get("HX-Request"):
            return render(request, self.partial_template_name, context)

        # En cualquier otro caso (o si no es HTMX), renderizar la plantilla completa
        return render(request, self.template_name, context)


import uuid
from django.shortcuts import render


@shared_task
def task_add_proteins( sci_name, task_id):
    cache.set(task_id, {'progress' :f"Organism validations...", 'info':"", 'warnings':""})
    organism, _ = Organism.get_or_create_organism(scientific_name=sci_name)
    cache.set(task_id, {'progress' :f"Getting organism proteins...", 'info':"", 'warnings':""})
    proteins = get_proteins_from_organism(organism)
    cache.set(task_id, {'progress': f"Getting proteins metadata...", 'info': "", 'warnings': ""})
    proteins_meta = get_protein_metadata(proteins)
    cache.set(task_id, {'progress': f"Adding organism proteins to database...", 'info': "", 'warnings': ""})
    created_proteins, not_inside_db= create_proteins_from_metadata(proteins_meta, organism)
    cache.set(task_id, {'progress': f"Task completed", 'info': "", 'warnings': f"{not_inside_db}"})
    print("fin")
    return created_proteins


# Vista para consultar progreso
def get_progress(request, task_id):
    progress = cache.get(task_id, {'progress': f"Not started", 'info': "", 'warnings': "patataa"})
    warnings ="hola"

    return render(request, "shared/progress_status.html", {"progress": progress,"warnings": warnings})

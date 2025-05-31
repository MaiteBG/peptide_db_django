from django.test import TestCase
import os
import django

from proteins.models import Protein
from proteins.services import get_proteins_from_organism, get_protein_metadata, create_proteins_from_metadata, \
    create_basic_database

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peptide_project.settings')
django.setup()

from catalog.models import Organism, Reference, Database, PeptideSequence

create_basic_database()


# Crear bases de datos con nombres claros

def test_func():
    organism, _ = Organism.get_or_create_organism(scientific_name="Allium")
    proteins = get_proteins_from_organism(organism)
    proteins_meta = get_protein_metadata(proteins)
    created_proteins = create_proteins_from_metadata(proteins_meta, organism)
    item, _ = created_proteins[0]
    print(item)
    print(item.__repr__())
    print(item.__format__())
    print(item.__format__("all"))


# Ejecutar la prueba
test_func()

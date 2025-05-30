from django.test import TestCase
import os
import django

from proteins.models import Protein

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peptide_project.settings')
django.setup()

from proteins.services import get_proteins_from_organism, get_protein_metadata, create_proteins_from_metadata

from catalog.models import Organism, Reference, Database, PeptideSequence


def test_peptidesequence_and_references():
    print(Organism.get_or_create_organism(scientific_name="Allium"))

# Ejecutar la prueba
test_peptidesequence_and_references()

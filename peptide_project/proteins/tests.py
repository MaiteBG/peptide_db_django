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
    ini_organisms = ["Allium", "Apium graveolens", "Beta vulgaris", "Brassica rapa", "Bos taurus"]
    # ini_organisms= [ "Capsicum", "Carassius", "Castanea sativa", "Ceratonia siliqua", "Cichorum intybus", "Citrus", "Corylus avellana", "Ctenopharyngodon", "Cucumis melo", "Cucumis sativus", "Cucurbita", "Cynara cardunculus",  "Euphasia","Foeniculum vulgare", "Fragaria ananassa", "Gadus"]
    # ini_organisms= [ "Gallus gallus", "Hypophthalmichthys", "Labeo", "Lactuca sativa", "Litopenaeus", "Malus domestica", "Meleagris gallopavo", "Olea europea", "Oncorhynchus", "Oreochromis"]
    # ini_organisms= [ "Oryctolagus cuniculus", "Ovis aries", "Pandalus", "Patinopecten", "Penaeus", "Petroselinum crispum", "Phaseolus vulgaris", "Pisum sativum", "Portunus", "Procambarus", "Prunus", "Punica granatum", "Pyrus", "Raphanus sativus", "Rubus idaeus","Sardina", "Solanum lycopersicum", "Solanum melongena"]
    for organism_name in ini_organisms:
        organism, _ = Organism.get_or_create_organism(scientific_name=organism_name)
        proteins = get_proteins_from_organism(organism)
        proteins_meta = get_protein_metadata(proteins)
        created_proteins = create_proteins_from_metadata(proteins_meta, organism)
        # item, _ = created_proteins[0]
        # print(item)
        # print(item.__repr__())
        # print(item.__format__())
        # print(item.__format__("all"))


# Ejecutar la prueba
test_func()

from django.test import TestCase
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peptide_project.settings')
django.setup()

from proteins.services import get_proteins_from_organism, get_protein_metadata, create_proteins_from_metadata
from catalog.models import Organism, Reference, Database, PeptideSequence

# Create your tests here.
'''

organism = Organism().create_from_scientific_name("Tenebrio molitor")


print(organism.__format__("all"))



accessions = get_proteins_from_organism(organism)
proteins = get_protein_metadata(accessions)

create_proteins_from_metadata(proteins,organism=organism )
# Ejemplo de uso:
for prot in proteins:
    print(prot)
    print(prot["sequence"])


'''


# result = Reference.get_reference_info_from_doi("10.1016/j.tibs.2011.12.002")
# print(result)


def test_peptidesequence_and_references():
    # Crear organismo
    org, _ = Organism.objects.get_or_create(scientific_name="Homo")

    # Crear bases de datos con nombres claros
    pubmed_db, _ = Database.objects.get_or_create(
        database_name="PubMed",
        url_pattern="https://pubmed.ncbi.nlm.nih.gov/{id}/"
    )
    doi_db, _ = Database.objects.get_or_create(
        database_name="DOI",
        url_pattern="https://doi.org/{id}"
    )
    swissprot_db, _ = Database.objects.get_or_create(
        database_name="UniProt Swiss-Prot",
        url_pattern="https://www.uniprot.org/uniprot/{id}"
    )
    trembl_db, _ = Database.objects.get_or_create(
        database_name="UniProt TrEMBL",
        url_pattern="https://www.uniprot.org/uniprot/{id}"
    )

    # Crear referencias
    pubmed_ref, _ = Reference.objects.get_or_create(
        doi=None,
        database=pubmed_db,
        db_accession="12345678"
    )
    doi_ref1, _ = Reference.objects.get_or_create(
        doi="10.1000/xyz123",
        database=doi_db,
        db_accession="XYZ123"
    )
    doi_ref2, _ = Reference.objects.get_or_create(
        doi="10.1000/abc456",
        database=doi_db,
        db_accession="ABC456"
    )
    swissprot_ref, _ = Reference.objects.get_or_create(
        doi=None,
        database=swissprot_db,
        db_accession="P12345"
    )
    trembl_ref, _ = Reference.objects.get_or_create(
        doi=None,
        database=trembl_db,
        db_accession="Q8N158"
    )

    # Crear secuencia peptídica
    peptide, _ = PeptideSequence.objects.get_or_create(
        aa_seq="MTEITAAMVKELRESTGAGMMDCKNALSETQHEK",
        organism=org,
        uniprot_code="P12345"
    )

    # Añadir referencias evitando duplicados
    def add_unique_reference(peptide_obj, reference_obj):
        exists = peptide_obj.references.filter(
            doi=reference_obj.doi,
            database=reference_obj.database,
            db_accession=reference_obj.db_accession
        ).exists()
        if not exists:
            peptide_obj.references.add(reference_obj)

    add_unique_reference(peptide, pubmed_ref)
    add_unique_reference(peptide, doi_ref1)
    add_unique_reference(peptide, doi_ref2)
    add_unique_reference(peptide, swissprot_ref)
    add_unique_reference(peptide, trembl_ref)

    peptide.save()

    # Mostrar resultados
    print(f"Peptide: {peptide}")
    print(f"References count: {peptide.references.count()}")  # Esperamos 5
    for ref in peptide.references.all():
        print(f" - Reference DOI: {ref.doi}, Database: {ref.database.database_name}, Accession: {ref.db_accession}")

    print(format(peptide, "all"))


# Ejecutar la prueba
test_peptidesequence_and_references()

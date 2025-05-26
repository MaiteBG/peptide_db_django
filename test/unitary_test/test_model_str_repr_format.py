import django
import pytest
from catalog.models import Organism, Reference, PeptideSequence, Protein

django.setup()


@pytest.fixture
def organism_instance():
    return Organism(
        scientific_name="Homo sapiens",
        common_name="Human",
        ncbi_url="https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=9606",
        class_name="Mammalia",
        subclass="Theria"
    )


@pytest.fixture
def reference_instance():
    return Reference(
        pmid_doi_db="PMID:123456",
        url="http://example.com"
    )


@pytest.fixture
def peptide_seq_instance(organism_instance, reference_instance):
    seq = PeptideSequence(
        aa_seq="MKWVTFISKWVTFISLLFLFSSAYSKWVTFISLLFLFSSAYSKWVTFISLLFLFSSAYSKWVTFISLLFLFSSAYSLLFLFSSAYSR",
        organism=organism_instance,
        reference=reference_instance,
        source="Experiment",
        uniprot_code="P12345",
        is_reviewed=True,
        date_added="2025-01-01"
    )
    seq.id = 3
    return seq


@pytest.fixture
def protein_instance(peptide_seq_instance):
    protein = Protein(
        id=7,
        protein_name="Hemoglobin",
        gene_name="HBB",
        sequence=peptide_seq_instance,
        protein_function="Oxygen transport"
    )
    return protein


# Tests Organism
def test_organism_str(organism_instance):
    expected = "Homo sapiens"
    assert str(organism_instance) == expected


def test_organism_repr(organism_instance):
    expected = ("<Organism(scientific_name='Homo sapiens', "
                "common_name='Human', "
                "ncbi_url='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=9606', "
                "class_name='Mammalia', subclass='Theria')>")
    assert repr(organism_instance) == expected


def test_organism_format_default(organism_instance):
    expected = "Organism: Homo sapiens (Human)"
    assert format(organism_instance) == expected


def test_organism_format_all(organism_instance):
    expected = (
        "Scientific Name: Homo sapiens\n"
        "Common Name: Human\n"
        "NCBI URL: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=9606\n"
        "Class: Mammalia\n"
        "Subclass: Theria"
    )
    assert format(organism_instance, "all") == expected


# Tests Reference
def test_reference_str(reference_instance):
    expected = "PMID:123456"
    assert str(reference_instance) == expected


def test_reference_repr(reference_instance):
    expected = "<Reference(pmid_doi_db='PMID:123456', url='http://example.com')>"
    assert repr(reference_instance) == expected


def test_reference_format_default(reference_instance):
    expected = "Reference: PMID:123456"
    assert format(reference_instance) == expected


def test_reference_format_all(reference_instance):
    expected = "Reference ID: PMID:123456\nURL: http://example.com"
    assert format(reference_instance, "all") == expected


# Tests PeptideSequence
def test_peptidesequence_str(peptide_seq_instance):
    # get_seq_preview corta la secuencia (máximo 30)
    expected_preview = "MKWVTFISKWVTF...YSLLFLFSSAYSR"
    assert str(peptide_seq_instance) == expected_preview


def test_peptidesequence_repr(peptide_seq_instance):
    expected = (f"<PeptideSequence(id=3, aa_seq='MKWVTFISKWVTF...YSLLFLFSSAYSR', "
                f"organism='Homo sapiens', reference='PMID:123456')>")
    assert repr(peptide_seq_instance) == expected


def test_peptidesequence_format_default(peptide_seq_instance):
    expected = (
        f"PeptideSequence #3: MKWVTFISKWVTF...YSLLFLFSSAYSR from Homo sapiens (Ref: PMID:123456) | Length: {len(peptide_seq_instance.aa_seq)}")
    assert format(peptide_seq_instance) == expected


def test_peptidesequence_format_all(peptide_seq_instance):
    expected = (
        f"ID: 3\n"
        f"Sequence: {peptide_seq_instance.aa_seq}\n"
        f"Sequence Length: {len(peptide_seq_instance.aa_seq)}\n"
        f"Organism: Homo sapiens\n"
        f"Reference: PMID:123456\n"
        f"Source: Experiment\n"
        f"UniProt code: P12345\n"
        f"Reviewed: Yes\n"
        f"Date added: 2025-01-01"
    )
    assert format(peptide_seq_instance, "all") == expected


# Tests Protein
def test_protein_str(protein_instance):
    expected_seq_str = format(protein_instance.sequence)
    expected = f"Hemoglobin (HBB) | {expected_seq_str}"
    assert str(protein_instance) == expected


def test_protein_repr(protein_instance):
    expected = ("<Protein(id=7, name='Hemoglobin', gene='HBB', "
                "organism='Homo sapiens', UniProt='P12345')>")
    assert repr(protein_instance) == expected


def test_protein_format_default(protein_instance):
    seq_format = format(protein_instance.sequence)
    expected = (f"Protein #7: Hemoglobin (HBB) | Organism: Homo sapiens | UniProt: P12345 | Sequence: {seq_format}")
    assert format(protein_instance) == expected


def test_protein_format_all(protein_instance):
    expected = (
        "ID: 7\n"
        "Protein Name: Hemoglobin\n"
        "Gene Name: HBB\n"
        "Organism: Homo sapiens\n"
        "UniProt Code: P12345\n"
        f"Sequence: {protein_instance.sequence.aa_seq}\n"
        "Protein Function: Oxygen transport\n"
    )
    assert format(protein_instance, "all") == expected

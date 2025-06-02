import re
import requests
from requests.adapters import HTTPAdapter, Retry
from catalog.models import Organism, PeptideSequence, Database
from proteins.models import Protein

# -------------------------------------------------------------------
# HTTP session setup with retry strategy for robustness in API calls
# -------------------------------------------------------------------
_session = requests.Session()
retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
_session.mount("https://", HTTPAdapter(max_retries=retries))

# -------------------------------------------------------------------
# Constants for UniProt API
# -------------------------------------------------------------------
# Template to fetch metadata for a list of accessions
UNIPROT_BASE_URL = (
    "https://rest.uniprot.org/uniprotkb/search?query={query}&format=json&size=100"
)


# Regular expression for extracting the next page link from HTTP headers
_re_next_link = re.compile(r'<(.+)>; rel="next"')


def create_basic_database():
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
    embl_db, _ = Database.objects.get_or_create(
        database_name="EMBL",
        url_pattern="https://www.ebi.ac.uk/ena/browser/view/{id}"
    )




def _get_next_link(headers: dict) -> str | None:
    """
    Extracts the 'next' pagination link from the response headers.

    Args:
        headers (dict): HTTP response headers.

    Returns:
        str | None: URL of the next page if available, otherwise None.
    """
    if "Link" in headers:
        match = _re_next_link.match(headers["Link"])
        if match:
            return match.group(1)
    return None

def _get_batches(initial_url: str):
    """
    Generator that yields paginated responses from UniProt API.

    Args:
        initial_url (str): The initial search URL.

    Yields:
        tuple: (response object, total number of results as string)
    """
    batch_url = initial_url
    while batch_url:
        response = _session.get(batch_url)
        response.raise_for_status()
        total = response.headers.get("x-total-results", "?")
        yield response, total
        batch_url = _get_next_link(response.headers)


def get_proteins_from_organism(organism: Organism) -> list[str]:
    """
    Retrieves a list of reviewed UniProt protein accessions for a given organism.

    Args:
        organism (Organism): A Django model instance representing the organism.

    Returns:
        list[str]: A list of UniProt accession IDs.
    """
    print(f"Fetching proteins for organism: {organism.scientific_name}")
    accns = []

    organism_ids = Organism.get_organism_NCBI_id(organism.scientific_name)
    search_url = Organism.build_uniprot_url_from_organism_ids(organism_ids)

    for batch, total in _get_batches(search_url):
        lines = batch.text.strip().splitlines()
        accns.extend(lines)
        print(f"Retrieved {len(accns)} / {total} proteins...")

    print(f"Finished fetching proteins for {organism.scientific_name}. Total: {len(accns)}")
    return accns


def extract_gene_name(gene_entry):
    """
    Extracts the most appropriate gene name from a dictionary.
    Priority: geneName > synonyms > orfNames
    """
    for key in gene_entry.keys():  # usually only 'geneName', but sometimes only have 'orfNames'
        if key in gene_entry:
            value = gene_entry[key]
            # Case 1: dict with 'value'
            if isinstance(value, dict) and 'value' in value:
                return value['value']
            # Case 2: list of dicts with 'value'
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and 'value' in item:
                        return item['value']
            # Case 3: plain string
            elif isinstance(value, str):
                return value
    return None  # No name found


def get_protein_metadata(accessions: list[str]) -> list[dict]:
    """
    Retrieves metadata for a list of UniProt protein accessions.

    Args:
        accessions (list[str]): A list of UniProt accession IDs.

    Returns:
        list[dict]: A list of dictionaries containing protein metadata, including citationCrossReferences.
    """
    results = []
    batch_size = 100  # Avoid overly long queries
    for acc in range(0, len(accessions), batch_size):
        batch = accessions[acc:acc + batch_size]
        query = " OR ".join([f"accession:{acc}" for acc in batch])
        url = UNIPROT_BASE_URL.format(query=query)
        response = _session.get(url)
        response.raise_for_status()
        data = response.json()

        for entry in data.get("results", []):
            acc = entry.get("primaryAccession")
            protein_name = (
                entry.get("proteinDescription", {})
                .get("recommendedName", {})
                .get("fullName", {})
                .get("value")
            )
            gene_names = entry.get("genes", [])
            gene_name = extract_gene_name(gene_names[0]) if gene_names else None
            comments = entry.get("comments", [])
            function = None
            for comment in comments:
                if comment["commentType"] == "FUNCTION":
                    texts = comment.get("texts", [])
                    if texts:
                        function = texts[0].get("value")
                        break

            sequence = entry.get("sequence", {}).get("value")

            # 🆕 Extraer todos los citationCrossReferences
            references = entry.get("references", [])
            all_cross_refs = [{'database': "UniProt Swiss-Prot", 'id': acc}]
            for ref in references:
                citation = ref.get("citation", {})
                cross_refs = citation.get("citationCrossReferences", [])
                if cross_refs:
                    all_cross_refs.extend(cross_refs)

            all_cross_refs.extend(entry.get("uniProtKBCrossReferences", []))


            results.append({
                "accession": acc,
                "protein_name": protein_name,
                "gene_name": gene_name,
                "protein_function": function,
                "sequence": sequence,
                "references": all_cross_refs,
            })

    return results

def create_proteins_from_metadata(proteins_metadata: list[dict], organism=None, reference=None):
    """
    Create Protein instances from a list of protein metadata dictionaries,
    only if a Protein with the same sequence, gene_name, and protein_name does not already exist.

    Args:
        proteins_metadata (list[dict]): List of protein metadata dictionaries.
        organism (Organism, optional): Organism to assign to the peptide sequences.
        reference (Reference, optional): Scientific reference to assign.

    Returns:
        list[Protein]: List of created Protein instances.
    """
    created_proteins = []

    for meta in proteins_metadata:
        seq_str = meta.get("sequence")
        if not seq_str:
            continue  # skip if no sequence info

        # Get or create peptide sequence
        sequence_obj, _ = PeptideSequence.objects.get_or_create(
            aa_seq=seq_str,
        )

        references = meta.get("references")
        sequence_obj.add_references(references)

        # Create protein instance
        try:
            protein = Protein.objects.get_or_create(
                sequence=sequence_obj,
                protein_name=meta.get("protein_name"),
                gene_name=meta.get("gene_name"),
                protein_function=meta.get("protein_function"),
                organism=organism,
                uniprot_code=meta.get("accession"),
            )
            created_proteins.append(protein)
        except Exception as e:
            print(e)

    return created_proteins

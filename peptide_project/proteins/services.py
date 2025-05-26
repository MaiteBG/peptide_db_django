import re
import requests
from requests.adapters import HTTPAdapter, Retry
from catalog.models import Organism, PeptideSequence
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

# Template to fetch reviewed protein accessions by organism name
BASE_URL = (
    "https://rest.uniprot.org/uniprotkb/search?"
    "query=reviewed:true+AND+organism_name:{}&size=500&format=list"
)

# Regular expression for extracting the next page link from HTTP headers
_re_next_link = re.compile(r'<(.+)>; rel="next"')


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
    search_url = BASE_URL.format(organism.scientific_name)

    for batch, total in _get_batches(search_url):
        lines = batch.text.strip().splitlines()
        accns.extend(lines)
        print(f"Retrieved {len(accns)} / {total} proteins...")

    print(f"Finished fetching proteins for {organism.scientific_name}. Total: {len(accns)}")
    return accns


def get_protein_metadata(accessions: list[str]) -> list[dict]:
    """
    Retrieves metadata for a list of UniProt protein accessions.

    Args:
        accessions (list[str]): A list of UniProt accession IDs.
        source (str, optional): Source tissue or other descriptor to add in each metadata dict.

    Returns:
        list[dict]: A list of dictionaries containing protein metadata.
    """
    results = []
    batch_size = 100  # Avoid overly long queries

    for i in range(0, len(accessions), batch_size):
        batch = accessions[i:i + batch_size]
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
            gene_name = gene_names[0]["geneName"]["value"] if gene_names else None

            comments = entry.get("comments", [])
            function = None
            for comment in comments:
                if comment["commentType"] == "FUNCTION":
                    texts = comment.get("texts", [])
                    if texts:
                        function = texts[0].get("value")
                        break

            sequence = entry.get("sequence", {}).get("value")

            results.append({
                "accession": acc,
                "protein_name": protein_name,
                "gene_name": gene_name,
                "protein_function": function,
                "sequence": sequence,
            })

    return results


def create_proteins_from_metadata(proteins_metadata: list[dict], organism=None, reference=None):
    """
    Create Protein instances from a list of protein metadata dictionaries.

    Each dict should include at least:
    - 'sequence': peptide sequence string (amino acid sequence)
    - 'protein_name', 'gene_name', 'protein_function', 'uniprot_code' (optional)

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

        # Busca o crea la secuencia PeptideSequence asociada
        sequence_obj, created = PeptideSequence.objects.get_or_create(
            aa_seq=seq_str,
            defaults={
                "organism": organism,
                "reference": reference,
                "uniprot_code": meta.get("accession"),
                "is_reviewed": True,  # asumiendo que viene de UniProt reviewed
                # Puedes añadir más campos aquí si los tienes en meta
            }
        )

        protein = Protein.objects.create(
            sequence=sequence_obj,
            protein_name=meta.get("protein_name"),
            gene_name=meta.get("gene_name"),
            protein_function=meta.get("protein_function"),
        )
        created_proteins.append(protein)

    return created_proteins

import requests
from Bio import Entrez
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

Entrez.email = "your.email@example.com"

# --- PeptideSequence Model ---

class PeptideSequence(models.Model):
    """
    Represents a unique peptide sequence associated with an organism
    and one or more scientific references.

    Attributes:
        aa_seq (TextField): Amino acid sequence of the peptide.
        organism (ForeignKey): Organism from which the peptide sequence originates.
        references (ManyToManyField): References linked to this peptide sequence.
        uniprot_code (CharField): Optional UniProt identifier.
        date_added (DateField): Timestamp when the entry was created.
    """

    aa_seq = models.TextField()
    organism = models.ForeignKey(
        'catalog.Organism', null=True, blank=True, on_delete=models.SET_NULL
    )
    references = models.ManyToManyField(
        'catalog.Reference', related_name='proteins'
    )
    uniprot_code = models.CharField(max_length=10, null=True, blank=True)
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['aa_seq', 'organism'],
                name='unique_peptideseq_org'
            )
        ]
        verbose_name = "Peptide Sequence"
        verbose_name_plural = "Peptide Sequences"

    def get_seq_preview(self, max_length=30):
        """
        Generate a truncated preview of the peptide sequence for display.

        If the sequence length exceeds max_length, it returns the first and last
        part separated by ellipsis (...).

        Args:
            max_length (int): Maximum length of the preview string (default 30).

        Returns:
            str: Truncated sequence preview or full sequence if short enough.
        """
        if len(self.aa_seq) <= max_length:
            return self.aa_seq
        half = (max_length - 3) // 2  # Reserve 3 chars for ellipsis
        return f"{self.aa_seq[:half]}...{self.aa_seq[-half:]}"

    def __str__(self):
        """
        Return a concise string representation of the peptide sequence,
        useful for admin panels or dropdown lists.

        Returns:
            str: Truncated sequence preview.
        """
        seq_preview = self.get_seq_preview()
        return f"{seq_preview}"

    def __repr__(self):
        """
        Return a detailed and unambiguous developer-friendly string
        representation of the instance.

        Includes instance id, truncated sequence, organism scientific name,
        and up to two associated references.

        Returns:
            str: Developer-focused representation string.
        """
        id_part = f"id={self.id}" if self.id else "unsaved"
        aa_seq_preview = self.get_seq_preview()
        organism = self.organism.scientific_name if self.organism else "No organism specified"
        refs = self.references.all()
        if refs.exists():
            ref_list = ", ".join(ref.__repr__() for ref in refs[:2])
        else:
            ref_list = "No references provided"

        return (
            f"<PeptideSequence({id_part}, aa_seq='{aa_seq_preview}', "
            f"organism='{organism}', references='{ref_list}')>"
        )

    def __format__(self, spec=None):
        """
        Format the instance into a string according to the given specifier.

        If spec == "all", returns a detailed multi-line report.
        Otherwise, returns a concise summary.

        Args:
            spec (str, optional): Format specifier, use "all" for full detail.

        Returns:
            str: Formatted string representation.
        """
        sequence_id = f"{self.id}" if self.id else "(unsaved)"
        seq_preview = self.get_seq_preview()
        organism_str = self.organism.scientific_name if self.organism else "Organism not specified"
        refs = self.references.all()

        if spec == "all":
            reference_str = "\n".join(
                ref.__format__("all") for ref in refs) if refs.exists() else "Reference not provided"
            format_str = (
                f"ID: {sequence_id}\n"
                f"Sequence: {self.aa_seq}\n"
                f"Sequence Length: {len(self.aa_seq)}\n"
                f"Organism: {organism_str}\n"
                f"References:\n{reference_str}\n"
                f"UniProt code: {self.uniprot_code or 'UniProt code not available'}\n"
                f"Date added to peptide_db: {self.date_added or 'Date not available'}"
            )
        else:
            reference_str = ", ".join(ref.__format__() for ref in refs) if refs.exists() else "Reference not provided"
            format_str = (
                f"PeptideSequence #{sequence_id}: {seq_preview} "
                f"from {organism_str} | Length: {len(self.aa_seq)} | (Refs: {reference_str}) "
            )

        return format_str

    def add_reference(self, reference):
        """
        Adds a Reference instance to this PeptideSequence's references if it
        does not already exist. Also validates that the organism associated
        with the peptide sequence and the reference match (if both are set).

        Args:
            reference (Reference): Reference instance to add.

        Raises:
            ValueError: If the organisms of the sequence and reference do not match.
        """
        # Validate organism match if both organisms exist
        if self.organism and hasattr(reference, 'organism') and reference.organism:
            if self.organism != reference.organism:
                raise ValueError(
                    "The organism of the peptide sequence and the reference do not match."
                )

        # Add reference only if not already associated
        if not self.references.filter(pk=reference.pk).exists():
            self.references.add(reference)




# --- Organism Model ---

class Organism(models.Model):
    """
    Represents an organism of origin, using its scientific name as the primary key.
    """

    scientific_name = models.CharField(max_length=50, primary_key=True)
    common_name = models.CharField(max_length=50, blank=True, null=True)
    kingdom = models.CharField(max_length=50, blank=True, null=True)
    phylum = models.CharField(max_length=50, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True, null=True)
    ncbi_url = models.URLField(max_length=120, blank=True, null=True)

    class Meta:
        verbose_name = "Organism"
        verbose_name_plural = "Organisms"

    @classmethod
    def create_from_scientific_name(cls, scientific_name: str):
        """
        Creates and saves an Organism instance based on the scientific name.

        If an organism with the given scientific name already exists in the database,
        it returns that existing instance instead of creating a new one.

        Args:
            scientific_name (str): The scientific name of the organism to find or create.

        Returns:
            Organism: The existing or newly created Organism instance.

        Raises:
            ValueError: If no organism data is found for the given scientific name.
        """
        # Check if organism already exists in the database
        existing = cls.objects.filter(scientific_name=scientific_name).first()
        if existing:
            return existing

        # Fetch organism data from external source (NCBI)
        organism_data = cls._find_organism_data(scientific_name)

        # Create and save new organism instance
        organism = cls(**organism_data)
        organism.save()
        return organism

    @staticmethod
    def _find_organism_data(scientific_name: str) -> dict:
        """
        Queries the NCBI Taxonomy database to find detailed information
        about an organism given its scientific name.

        Args:
            scientific_name (str): The scientific name to search for.

        Returns:
            dict: A dictionary with organism data including scientific name,
                  common name, kingdom, phylum, class name, and NCBI URL.

        Raises:
            ValueError: If no organism or exact match is found for the given name.
        """
        # Search taxonomy database for the scientific name
        with Entrez.esearch(db="taxonomy", term=scientific_name) as handle:
            record = Entrez.read(handle)
        id_list = record.get("IdList", [])

        # If no IDs returned, organism does not exist in NCBI
        if not id_list:
            raise ValueError(f"No organism found for '{scientific_name}'")

        # For each tax_id found, fetch detailed taxonomy record
        for tax_id in id_list:
            with Entrez.efetch(db="taxonomy", id=tax_id, retmode="xml") as handle:
                records = Entrez.read(handle)

            # Check for exact scientific name match in returned records
            for rec in records:
                if rec["ScientificName"].lower() == scientific_name.lower():
                    # Build lineage dictionary: rank -> scientific name
                    lineage = {item["Rank"]: item["ScientificName"] for item in rec.get("LineageEx", [])}

                    # Return the organism data extracted
                    return {
                        "scientific_name": scientific_name,
                        "common_name": rec.get("OtherNames", {}).get("GenbankCommonName"),
                        "kingdom": lineage.get("kingdom"),
                        "phylum": lineage.get("phylum"),
                        "class_name": lineage.get("class"),
                        "ncbi_url": f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={tax_id}"
                    }

        # If no exact match found, raise an error
        raise ValueError(f"No exact match found for '{scientific_name}'")


    def __str__(self):
        """
        Returns a string representation of the organism.

        Typically returns the scientific name of the organism.
        If not available, a default message is shown.
        """
        return self.scientific_name or "Scientific name not specified"

    def __repr__(self):
        """
        Returns a developer-friendly representation of the organism instance.

        Includes scientific name, common name, NCBI URL, kingdom, phylum, and class name,
        with fallback messages for any missing fields.
        """
        common = self.common_name or "Common name not specified"
        ncbi = self.ncbi_url or "NCBI URL not provided"
        kingdom = self.kingdom or "Kingdom not specified"
        phylum = self.phylum or "Phylum not specified"
        class_name = self.class_name or "Class not specified"
        return (f"<Organism(scientific_name='{self.scientific_name}', "
                f"common_name='{common}', kingdom='{kingdom}', phylum='{phylum}', "
                f"class_name='{class_name}', ncbi_url='{ncbi}')>")

    def __format__(self, spec=None):
        """
        Custom string formatting for the organism instance.

        If `spec == "all"`, returns a multiline detailed view of the organism.
        Otherwise, returns a compact representation with scientific and common name.

        Args:
            spec (str): Optional format specifier, e.g., "all".

        Returns:
            str: Formatted string based on the provided spec.
        """
        sci_name = self.scientific_name or "Scientific name not specified"
        common = self.common_name or "Common name not specified"
        ncbi = self.ncbi_url or "NCBI URL not provided"
        kingdom = self.kingdom or "Kingdom not specified"
        phylum = self.phylum or "Phylum not specified"
        class_name = self.class_name or "Class not specified"

        if spec == "all":
            return (
                f"Scientific Name: {sci_name}\n"
                f"Common Name: {common}\n"
                f"NCBI URL: {ncbi}\n"
                f"Kingdom: {kingdom}\n"
                f"Phylum: {phylum}\n"
                f"Class: {class_name}\n"
            )
        else:
            return f"Organism: {sci_name} ({common})"


class Database(models.Model):
    """
    Stores a scientific database.
    """
    database_name = models.CharField(max_length=100, blank=True, primary_key=True)
    url_pattern = models.URLField(blank=True, null=True)
    default_url = models.URLField(blank=True, null=True)

    def __str__(self):
        """
        Return a simple string representation of the database.

        Returns:
            str: The database name or a placeholder if not set.
        """
        return self.database_name or "Unnamed Database"

    def __repr__(self):
        """
        Return a detailed, developer-friendly string representation of the database.

        Returns:
            str: Formatted string with database name and URL pattern.
        """
        name = self.database_name or "(no name)"
        url_pat = self.url_pattern or "(no url pattern)"
        return f"<Database(database_name='{name}', url_pattern='{url_pat}')>"

    def __format__(self, spec=None):
        """
        Provide custom formatted string representations.

        If spec == "all", returns detailed multiline information.
        Otherwise, returns the database name.

        Args:
            spec (str, optional): Format specifier.

        Returns:
            str: Formatted string based on the spec.
        """
        if spec == "all":
            return (
                f"Database Name: {self.database_name or '(no name)'}\n"
                f"URL Pattern: {self.url_pattern or '(no url pattern)'}\n"
                f"Default URL: {self.default_url or '(no default url)'}"
            )
        else:
            return str(self)


# --- Reference Model ---

class Reference(models.Model):
    """
    Stores a scientific reference identifier (PMID, DOI, or other).
    """
    database = models.ForeignKey('catalog.Database', null=True, blank=True, on_delete=models.SET_NULL)
    db_accession = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['database', 'db_accession'],
                name='unique_database_db_accession',
                condition=Q(db_accession__isnull=False)  # Only if db_accession is null
            )
        ]
        verbose_name = "Reference"
        verbose_name_plural = "References"

    @staticmethod
    def get_reference_info_from_doi(doi) -> dict | None:
        """
        Fetches bibliographic information for a given DOI using the CrossRef API.

        Args:
            doi (str): The DOI string.

        Returns:
            dict | None: A dictionary with bibliographic info including title, authors,
                         journal, year, publisher, URL, etc. Returns None if not found.
        """

        url = f"https://api.crossref.org/works/{doi}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            # CrossRef stores main info under 'message'
            message = data.get("message", {})

            # Parse authors as list of strings "Firstname Lastname"
            authors = []
            for author in message.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                full_name = f"{given} {family}".strip()
                if full_name:
                    authors.append(full_name)

            # Prepare result dict
            result = {
                "title": message.get("title", [""])[0],  # Title is a list
                "authors": authors,
                "journal": message.get("container-title", [""])[0],  # Journal or book title
                "year": message.get("published-print", {}).get("date-parts", [[None]])[0][0] or
                        message.get("published-online", {}).get("date-parts", [[None]])[0][0],
                "publisher": message.get("publisher"),
                "doi": doi,
                "url": message.get("URL"),
                "type": message.get("type"),
            }

            return result

        except requests.HTTPError as e:
            print(f"HTTP error when fetching DOI {doi}: {e}")
            return None
        except Exception as e:
            print(f"Error when fetching DOI {doi}: {e}")
            return None

    # def get_reference_info_from_database(self):

    def __str__(self):
        """
        Returns a simple string representation of the Reference,
        showing the primary identifier (DOI or db_accession).

        Returns:
            str: The reference ID or a placeholder if not set.
        """
        # Prefer DOI, then db_accession, else placeholder
        return f"{self.database}: {self.db_accession or 'No reference ID'}"

    def __repr__(self):
        """
        Returns a detailed developer-friendly string representation
        of the Reference, including the DOI, database, and accession.

        Returns:
            str: A formatted string showing key fields.
        """
        db_name = f"{self.database.database_name} ({self.database.url_pattern.replace('{id}', self.db_accession)})" if self.database and self.database.url_pattern and self.db_accession else "(no database)"
        accession_str = self.db_accession or "(no accession)"
        return f"<Reference( database='{db_name}', db_accession='{accession_str}')>"

    def __format__(self, spec=None):
        """
        Provides custom formatted string representations of the Reference.
        If spec is 'all', returns detailed multiline information;
        otherwise, returns a brief representation.

        Args:
            spec (str, optional): Format specification. Defaults to None.

        Returns:
            str: Formatted string based on the spec.
        """

        accession_str = self.db_accession or "(no accession)"

        if spec == "all":

            return (
                f"Database: {self.database.database_name}\n"
                f"\tAccession: {accession_str}\n"
                f"\tURL: {self.database.url_pattern.replace('{id}', self.db_accession)}\n"
            )
        else:
            # Brief single line summary
            return f"{self.database}: {self.db_accession or 'No reference ID'}"

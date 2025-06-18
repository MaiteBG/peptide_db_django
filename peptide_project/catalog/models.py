import hashlib

import requests
from Bio import Entrez
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

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
    peptideseq_hash = models.CharField(max_length=32, unique=True, editable=False)
    references = models.ManyToManyField('catalog.Reference', related_name='references')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['peptideseq_hash'],
                name='unique_peptideseq'
            )
        ]
        verbose_name = "Peptide Sequence"
        verbose_name_plural = "Peptide Sequences"

    def save(self, *args, **kwargs):
        if self.aa_seq:
            self.peptideseq_hash = hashlib.md5(self.aa_seq.encode("utf-8")).hexdigest()
        super().save(*args, **kwargs)

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
        refs = self.references.order_by('database', 'db_accession')
        if refs.exists():
            ref_list = ", ".join(ref.__repr__() for ref in refs[:2])
        else:
            ref_list = "No references provided"

        return (
            f"<PeptideSequence({id_part}, aa_seq='{aa_seq_preview}', references='{ref_list}')>"
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
        refs = self.references.order_by('database', 'db_accession')


        if spec == "all":
            reference_str = "\n".join(
                ref.__format__("all") for ref in refs) if refs.exists() else "Reference not provided"
            format_str = (
                f"ID: {sequence_id}\n"
                f"Sequence: {self.aa_seq}\n"
                f"Sequence Length: {len(self.aa_seq)}\n"
                f"References:\n{reference_str}\n"
            )
        else:
            reference_str = ", ".join(ref.__format__() for ref in refs) if refs.exists() else "Reference not provided"
            format_str = (
                f"PeptideSequence #{sequence_id}: {seq_preview} | Length: {len(self.aa_seq)} | (Refs: {reference_str}) "
            )

        return format_str

    def add_references(self, references):
        replacements = {
            # to add replacements
        }

        for ref in references:
            db_name = ref.get("database")
            db_name = replacements.get(db_name, db_name)
            external_id = ref.get("id")
            if not db_name or not external_id:
                continue  # skip invalid ref

            try:
                database = Database.objects.get(pk=db_name)

                reference, was_created = Reference.objects.get_or_create(
                    database=database,
                    db_accession=external_id
                )
                self.references.add(reference)

            except Database.DoesNotExist:
                # print(f"La base de datos '{db_name}' no existe.")
                continue


# --- Organism Model ---

class Organism(models.Model):
    """
    Represents an organism of origin, using its scientific name as the primary key.
    """

    scientific_name = models.CharField(max_length=50, primary_key=True)
    common_name = models.CharField(max_length=50, blank=True, null=True)
    kingdom = models.CharField(max_length=50, blank=True, null=True,
                               help_text=("Taxonomic Kingdom"))
    phylum = models.CharField(max_length=50, blank=True, null=True,
                              help_text=("Taxonomic Phylum"))
    class_name = models.CharField(max_length=50, blank=True, null=True,
                                  help_text=("Taxonomic Class"))
    ncbi_url = models.URLField(max_length=120, blank=True, null=True)

    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        verbose_name = "Organism"
        verbose_name_plural = "Organisms"

    @property
    def slug(self):
        return slugify(self.scientific_name)

    @staticmethod
    def get_organism_NCBI_id(scientific_name):
        # Search taxonomy database for the scientific name
        try:
            with Entrez.esearch(db="taxonomy", term=scientific_name) as handle:
                record = Entrez.read(handle)
            id_list = record.get("IdList", [])
            # If no IDs returned, organism does not exist in NCBI
            if not id_list:
                raise ValueError(f"No organism found for '{scientific_name}'")
            return id_list
        except Exception:
            raise ValueError(f"Error searching organism '{scientific_name}'")

    @staticmethod
    def build_uniprot_url_from_organism_ids(organism_ids, size=500, format="list"):
        """
        Construye una URL de búsqueda para UniProt con múltiples organism_id.

        Args:
            organism_ids (list of int): Lista de NCBI Taxonomy IDs.
            size (int): Número de resultados por página (máx 500).
            format (str): Formato de salida (ej. "list", "json", etc.)

        Returns:
            str: URL completa para hacer la petición.
        """
        if not organism_ids:
            raise ValueError("La lista de organism_ids no puede estar vacía.")

        organism_query = "+OR+".join(f"taxonomy_id:{oid}" for oid in organism_ids)
        full_query = f"reviewed:true+AND+({organism_query})"
        base_url = "https://rest.uniprot.org/uniprotkb/search"

        return f"{base_url}?query={full_query}&size={size}&format={format}"

    @classmethod
    def _find_organism_data(cls, scientific_name: str) -> dict:
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

        id_list = cls.get_organism_NCBI_id(scientific_name)

        # For each tax_id found, fetch detailed taxonomy record
        for tax_id in id_list:
            with Entrez.efetch(db="taxonomy", id=tax_id, retmode="xml") as handle:
                records = Entrez.read(handle)

            # Check for exact scientific name match in returned records
            for rec in records:
                # Obtain synonym names
                synonyms = rec.get("OtherNames", {}).get("Synonym", [])
                synonyms_lower = [s.lower() for s in synonyms]

                if (rec["ScientificName"].lower() == scientific_name.lower()
                        or scientific_name.lower() in synonyms_lower):  # or synonym
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

    @classmethod
    def get_or_create_organism(csl, **kwargs):
        if len(kwargs) == 1:
            # Caso: solo se pasa el scientific_name
            _, scientific_name = next(iter(kwargs.items()))

            try:
                data = Organism._find_organism_data(scientific_name)
                organism, created = Organism.objects.get_or_create(scientific_name=data["scientific_name"],
                                                                   defaults=data)
                return organism, created
            except ValueError as e:
                raise ValueError(f"{e}")

        # Caso general: usar get_or_create con lo que se pasa
        organism, created = Organism.objects.get_or_create(**kwargs)
        return organism, created

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
                f"\tCommon Name: {common}\n"
                f"\tNCBI URL: {ncbi}\n"
                f"\tKingdom: {kingdom}\n"
                f"\tPhylum: {phylum}\n"
                f"\tClass: {class_name}\n"
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
        if spec == "html":
            return (
                f"{self.database.database_name}: <a href= {self.database.url_pattern.replace('{id}', self.db_accession)} target='blank'> {accession_str} </a>"
            )
        else:
            # Brief single line summary
            return f"{self.database}: {self.db_accession or 'No reference ID'}"

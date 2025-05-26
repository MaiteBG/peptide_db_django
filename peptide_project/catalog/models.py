from Bio import Entrez
from django.db import models

Entrez.email = "your.email@example.com"

# --- PeptideSequence Model ---

class PeptideSequence(models.Model):
    """
    Represents a unique peptide sequence.
    Includes information about its source, scientific reference, and originating organism.
    """

    aa_seq = models.TextField()  # Amino acid sequence of the peptide
    organism = models.ForeignKey(
        'catalog.Organism', null=True, blank=True, on_delete=models.SET_NULL)  # Link to the originating organism
    reference = models.ForeignKey(
        'catalog.Reference', null=True, blank=True, on_delete=models.SET_NULL)  # Link to the scientific reference
    source = models.CharField(max_length=100, null=True, blank=True)  # Experimental or literature source
    uniprot_code = models.CharField(max_length=10, null=True, blank=True)  # Optional UniProt identifier
    is_reviewed = models.BooleanField(default=False)  # Whether the sequence has been curated/reviewed
    date_added = models.DateField(auto_now_add=True)  # Automatically set date when entry is created

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['aa_seq', 'source', 'organism', 'reference'],
                name='unique_peptideseq_source_org_ref'
            )
        ]
        verbose_name = "Peptide Sequence"
        verbose_name_plural = "Peptide Sequences"

    def get_seq_preview(self, max_length=30):
        """
        Returns a truncated preview of the peptide sequence.

        If the sequence is longer than `max_length`, it returns a preview
        showing the beginning and end of the sequence with an ellipsis (...) in the middle.

        Args:
            max_length (int): Maximum number of characters to display (including ellipsis).

        Returns:
            str: Truncated sequence preview or the full sequence if short enough.
        """
        if len(self.aa_seq) <= max_length:
            return self.aa_seq
        half = (max_length - 3) // 2  # Leave space for ellipsis (...)
        return f"{self.aa_seq[:half]}...{self.aa_seq[-half:]}"

    def __str__(self):
        """
        Returns a short string representation of the peptide sequence.

        Useful for displaying the object in admin panels or dropdowns.

        Returns:
            str: A truncated sequence preview.
        """
        seq_preview = self.get_seq_preview()
        return f"{seq_preview}"

    def __repr__(self):
        """
        Returns a detailed, unambiguous string representation for developers.

        Includes object ID (if saved), truncated sequence, organism, and reference.

        Returns:
            str: Developer-friendly representation of the peptide sequence instance.
        """
        id_part = f"id={self.id}" if self.id else "unsaved"
        aa_seq_preview = self.get_seq_preview()
        organism = (self.organism and self.organism.scientific_name) or "No organism specified"
        reference = (self.reference and self.reference.pmid_doi_db) or "No reference provided"

        return (
            f"<PeptideSequence({id_part}, aa_seq='{aa_seq_preview}', "
            f"organism='{organism}', reference='{reference}')>"
        )

    def __format__(self, spec=None):
        """
        Returns a formatted string representation based on the given specifier.

        If `spec == "all"`, returns a detailed multiline report.
        Otherwise, returns a concise summary of the peptide sequence.

        Args:
            spec (str, optional): Format specifier. Use "all" for full detail.

        Returns:
            str: Formatted string representation of the peptide sequence.
        """
        sequence_id = f"{self.id}" if self.id else "(unsaved)"
        seq_preview = self.get_seq_preview()
        organism_str = (self.organism and self.organism.scientific_name) or "Organism not specified"
        reference_str = (self.reference and self.reference.pmid_doi_db) or "Reference not provided"

        if spec == "all":
            format_str = (
                f"ID: {sequence_id}\n"
                f"Sequence: {self.aa_seq}\n"
                f"Sequence Length: {len(self.aa_seq)}\n"
                f"Organism: {organism_str}\n"
                f"Reference: {reference_str}\n"
                f"Source: {self.source or 'Source not specified'}\n"
                f"UniProt code: {self.uniprot_code or 'UniProt code not available'}\n"
                f"Reviewed: {'Yes' if self.is_reviewed else 'No'}\n"
                f"Date added: {self.date_added or 'Date not available'}"
            )
        else:
            format_str = (
                f"PeptideSequence #{sequence_id}: {seq_preview} "
                f"from {organism_str} (Ref: {reference_str}) | Length: {len(self.aa_seq)}"
            )

        return format_str


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


# --- Reference Model ---

class Reference(models.Model):
    """
    Stores a scientific reference identifier (PMID, DOI, or other).
    """

    pmid_doi_db = models.CharField(max_length=40, primary_key=True)
    url = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        """
        Returns a simple string representation of the Reference,
        showing the primary identifier (PMID or DOI).

        Returns:
            str: The reference ID or a placeholder if not set.
        """
        return self.pmid_doi_db or "No reference ID"

    def __repr__(self):
        """
        Returns a detailed developer-friendly string representation
        of the Reference, including the ID and URL.

        Returns:
            str: A formatted string showing key fields.
        """
        ref_id = self.pmid_doi_db or "(unsaved)"
        url = self.url or "No URL"
        return f"<Reference(pmid_doi_db='{ref_id}', url='{url}')>"

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
        ref_id = self.pmid_doi_db or "(unsaved)"
        url = self.url or "No URL"

        if spec == "all":
            return (
                f"Reference ID: {ref_id}\n"
                f"URL: {url}"
            )
        else:
            return f"Reference: {ref_id}"

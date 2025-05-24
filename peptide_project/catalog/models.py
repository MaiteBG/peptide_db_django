from django.core.exceptions import ValidationError
from django.db import models


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
    ncbi_url = models.URLField(max_length=120, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True, null=True)
    subclass = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Organism"
        verbose_name_plural = "Organisms"

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

        Includes scientific name, common name, NCBI URL, class name, and subclass,
        with fallback messages for any missing fields.
        """
        common = self.common_name or "Common name not specified"
        ncbi = self.ncbi_url or "NCBI URL not provided"
        class_name = self.class_name or "Class not specified"
        subclass = self.subclass or "Subclass not specified"
        return (f"<Organism(scientific_name='{self.scientific_name}', "
                f"common_name='{common}', ncbi_url='{ncbi}', "
                f"class_name='{class_name}', subclass='{subclass}')>")

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
        class_name = self.class_name or "Class not specified"
        subclass = self.subclass or "Subclass not specified"

        if spec == "all":
            return (
                f"Scientific Name: {sci_name}\n"
                f"Common Name: {common}\n"
                f"NCBI URL: {ncbi}\n"
                f"Class: {class_name}\n"
                f"Subclass: {subclass}"
            )
        else:
            return f"Organism: {sci_name} ({common})"


# --- Protein Model ---

class Protein(models.Model):
    """
    Protein model referencing the peptide sequence and additional protein-specific info.
    """

    sequence = models.ForeignKey(PeptideSequence, on_delete=models.CASCADE, related_name='proteins')
    protein_name = models.CharField(max_length=150, blank=True, null=True)
    gene_name = models.CharField(max_length=100, blank=True, null=True)
    protein_function = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['sequence', 'gene_name', 'protein_name'],
                name='unique_protein_by_sequence_gene_name_and_name'
            )
        ]
        verbose_name = "Protein"
        verbose_name_plural = "Proteins"

    def clean(self):
        """
        Validates that the related peptide sequence has both organism and reference defined.
        """
        if not self.sequence.organism:
            raise ValidationError("Protein must have an organism.")
        if not self.sequence.reference:
            raise ValidationError("Protein must have a reference.")

    def save(self, *args, **kwargs):
        """
        Perform validation before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns a concise string representation of the protein.

        Includes the protein name, gene name, and a formatted version of its sequence,
        if available.

        Returns:
            str: A human-readable string summarizing the protein.
        """
        protein_name = self.protein_name or "Unnamed protein"
        gene_name = self.gene_name or "No gene name"
        sequence_str = format(self.sequence) if self.sequence else "(No sequence)"
        return f"{protein_name} ({gene_name}) | {sequence_str}"

    def __repr__(self):
        """
        Returns a detailed developer-oriented string representation of the protein.

        Includes the database ID, protein name, gene name, organism, and UniProt code.

        Returns:
            str: A developer-friendly string representing the protein instance.
        """
        id_part = f"id={self.id}" if self.id else "unsaved"
        protein_name = self.protein_name or "Unnamed protein"
        gene_name = self.gene_name or "No gene name"
        organism = getattr(self.sequence.organism, "scientific_name", "No organism") if self.sequence else "No organism"
        uniprot_code = self.sequence.uniprot_code or "No UniProt code" if self.sequence else "No UniProt code"

        return (f"<Protein({id_part}, name='{protein_name}', gene='{gene_name}', "
                f"organism='{organism}', UniProt='{uniprot_code}')>")

    def __format__(self, spec=None):
        """
        Returns a custom formatted string representation of the protein.

        If `spec == "all"`, includes detailed multiline information including sequence and function.
        Otherwise, provides a brief summary of the protein.

        Args:
            spec (str, optional): Format specifier. Use "all" for full detail.

        Returns:
            str: A formatted string representing the protein.
        """
        id_part = f"{self.id}" if self.id else "(unsaved)"
        protein_name = self.protein_name or "Unnamed protein"
        gene_name = self.gene_name or "No gene name"
        organism = getattr(self.sequence.organism, "scientific_name", "No organism") if self.sequence else "No organism"
        uniprot_code = self.sequence.uniprot_code or "No UniProt code" if self.sequence else "No UniProt code"
        seq_format = format(self.sequence, spec) if self.sequence else "(No sequence)"

        if spec == "all":
            format_str = (
                f"ID: {id_part}\n"
                f"Protein Name: {protein_name}\n"
                f"Gene Name: {gene_name}\n"
                f"Organism: {organism}\n"
                f"UniProt Code: {uniprot_code}\n"
                f"Sequence: {self.sequence.aa_seq if self.sequence else 'N/A'}\n"
                f"Protein Function: {self.protein_function or 'N/A'}\n"
            )
        else:
            format_str = (
                f"Protein #{id_part}: {protein_name} ({gene_name}) | "
                f"Organism: {organism} | UniProt: {uniprot_code} | Sequence: {seq_format}"
            )

        return format_str


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

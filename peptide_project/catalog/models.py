from django.core.exceptions import ValidationError
from django.db import models


class PeptideSequence(models.Model):
    """
    Represents a unique peptide sequence.
    Includes information about its source, scientific reference, and originating organism.
    """
    aa_seq = models.TextField()
    uniprot_code = models.CharField(max_length=10, null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    organism = models.ForeignKey('catalog.Organism', null=True, blank=True, on_delete=models.SET_NULL)
    reference = models.ForeignKey('catalog.Reference', null=True, blank=True, on_delete=models.SET_NULL)
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['aa_seq', 'source', 'organism', 'reference'],
                name='unique_peptideseq_source_org_ref'
            )
        ]
        verbose_name = "Peptide Sequence"
        verbose_name_plural = "Peptide Sequences"


class Organism(models.Model):
    """
    Represents an organism of origin, using its scientific name as the primary key.
    """
    scientific_name = models.CharField(max_length=50, primary_key=True)
    common_name = models.CharField(max_length=50, blank=True, null=True)
    ncbi_url = models.URLField(max_length=120, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True, null=True)
    subclass = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        """Returns the scientific name of the organism."""
        return self.scientific_name


class Protein(models.Model):
    """
    Protein model referencing the peptide sequence and additional protein-specific info.
    """
    sequence = models.ForeignKey(PeptideSequence, on_delete=models.CASCADE, related_name='proteins')
    protein_name = models.CharField(max_length=150, blank=True, null=True)
    gene_name = models.CharField(max_length=100, blank=True, null=True)
    protein_function = models.TextField(blank=True, null=True)
    sequence_length = models.PositiveIntegerField(blank=True, null=True)
    is_reviewed = models.BooleanField(default=False)

    def clean(self):
        # Validate that organism is set
        if not self.sequence.organism:
            raise ValidationError("Protein must have an organism.")

        # Validate that reference is set
        if not self.sequence.reference:
            raise ValidationError("Protein must have a reference.")

    def save(self, *args, **kwargs):
        # Run full validation including calling clean() before saving
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        # Return the protein name if set, otherwise a generic label with the ID
        return self.protein_name or f"Protein {self.id}"


class Reference(models.Model):
    """
    Stores a scientific reference identifier (PMID, DOI, or other).
    """
    pmid_doi_db = models.CharField(max_length=40, primary_key=True)
    url = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        """Returns the reference identifier (e.g., PMID or DOI)."""
        return self.pmid_doi_db



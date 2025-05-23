from django.db import models
from catalog.models import PeptideSequence, Reference


class Bioactivity(models.Model):
    """
    Describes a specific bioactivity type of a peptide.
    """
    BIOACTIVITY_TYPES = (
        ('quantitative', 'Quantitative'),
        ('non_quantitative', 'Non-Quantitative'),
    )

    name = models.CharField(max_length=50)
    target = models.CharField(max_length=50)
    effect = models.CharField(max_length=50)
    activity_type = models.CharField(max_length=20, choices=BIOACTIVITY_TYPES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'target', 'effect', 'activity_type'],
                name='unique_bioactivity_name_target_effect_type'
            )
        ]

    def __str__(self):
        return f"{self.name} on {self.target} ({self.activity_type})"


class Peptide(models.Model):
    """
    Represents a peptide, derived from a peptide sequence, with biological activity.
    """
    sequence = models.ForeignKey(PeptideSequence, on_delete=models.CASCADE)
    bioactivities = models.ManyToManyField(Bioactivity, through='PeptideBioactivityInfo')
    peptide_info_source = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Peptide {self.sequence.aa_seq}"


class PeptideBioactivityInfo(models.Model):
    """
    Intermediate model for additional data on the peptide-bioactivity relationship.
    """
    peptide = models.ForeignKey(Peptide, on_delete=models.CASCADE)
    bioactivity = models.ForeignKey(Bioactivity, on_delete=models.CASCADE)
    original_value = models.CharField(max_length=50, blank=True, null=True)
    value = models.FloatField(blank=True, null=True)
    other_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.peptide} - {self.bioactivity}"


class Protease(models.Model):
    """
    Represents a protease enzyme that cleaves peptide bonds.
    """
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    ec_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'source'],
                name='unique_protease_name_source'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.source})"


class CleavageReference(models.Model):
    protease = models.ForeignKey(Protease, on_delete=models.CASCADE)
    substrate_formula = models.CharField(max_length=200)
    ref = models.ForeignKey(Reference, on_delete=models.CASCADE)
    substrate_name = models.CharField(max_length=200)
    uniprot_substrate = models.CharField(max_length=10)
    site_P4 = models.CharField(max_length=5)
    site_P3 = models.CharField(max_length=5)
    site_P2 = models.CharField(max_length=5)
    site_P1 = models.CharField(max_length=5)
    site_P1prime = models.CharField(max_length=5)
    site_P2prime = models.CharField(max_length=5)
    site_P3prime = models.CharField(max_length=5)
    site_P4prime = models.CharField(max_length=5)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'protease', 'substrate_formula', 'ref', 'substrate_name',
                    'site_P4', 'site_P3', 'site_P2', 'site_P1',
                    'site_P1prime', 'site_P2prime', 'site_P3prime', 'site_P4prime'
                ],
                name='unique_cleavage_reference'
            )
        ]
        verbose_name = "Cleavage Reference"
        verbose_name_plural = "Cleavage References"

    def __str__(self):
        return f"Cleavage by {self.protease} on {self.substrate_name} ({self.ref})"

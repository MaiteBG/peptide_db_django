from django.core.exceptions import ValidationError
from django.db import models

from catalog.models import PeptideSequence


# --- Protein Model ---

class Protein(models.Model):
    """
    Protein model referencing the peptide sequence and additional protein-specific info.
    """

    sequence = models.ForeignKey(PeptideSequence, on_delete=models.CASCADE)
    protein_name = models.CharField(max_length=150, blank=True, null=True)
    gene_name = models.CharField(max_length=100, blank=True, null=True)
    protein_function = models.TextField(blank=True, null=True)
    organism = models.ForeignKey(
        'catalog.Organism', null=True, blank=True, on_delete=models.SET_NULL
    )
    uniprot_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['sequence', 'gene_name', 'protein_name'],
                name='unique_protein_by_sequence_gene_name_and_name'
            )
        ]
        verbose_name = "Protein"
        verbose_name_plural = "Proteins"

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
        organism = getattr(self.organism, "scientific_name", "No organism") if self.organism else "No organism"
        uniprot_code = self.uniprot_code or "No UniProt code" if self.uniprot_code else "No UniProt code"

        return (f"<Protein({id_part}, name='{protein_name}', gene='{gene_name}', "
                f"organism='{organism}', UniProt='{uniprot_code}')>")

    def __format__(self, spec=""):
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
        organism = getattr(self.organism, "scientific_name", "No organism")
        uniprot_code = self.uniprot_code or "No UniProt code"
        seq_format = format(self.sequence, spec) if self.sequence else "(No sequence)"

        if spec == "all":
            format_str = (
                f"ID: {id_part}\n"
                f"Protein Name: {protein_name}\n"
                f"Gene Name: {gene_name}\n"
                f"Organism: {organism}\n"
                f"UniProt Code: {uniprot_code}\n"
                f"Sequence: {seq_format}\n"
            )
        else:
            format_str = (
                f"Protein #{id_part}: {protein_name} ({gene_name}) | "
                f"Organism: {organism} | UniProt: {uniprot_code} | Sequence: {seq_format}"
            )

        return format_str

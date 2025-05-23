from django.db import models


class Organism(models.Model):
    scientific_name = models.CharField(max_length=50, primary_key=True)
    common_name = models.CharField(max_length=50, blank=True, null=True)
    ncbi_url = models.URLField(max_length=120, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True, null=True)
    subclass = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.scientific_name


class Reference(models.Model):
    pmid_doi_db = models.CharField(max_length=40, primary_key=True)
    url = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.pmid_doi_db


class UserActionLog(models.Model):
    log_date = models.DateTimeField(auto_now_add=True)
    contact_name = models.CharField(max_length=100)
    organization_name = models.CharField(max_length=100)
    email = models.EmailField()
    action = models.CharField(max_length=20)
    action_info = models.TextField(blank=True, null=True)
    allow_commercial = models.BooleanField()

    def __str__(self):
        return f"{self.action} by {self.contact_name} on {self.log_date:%Y-%m-%d}"

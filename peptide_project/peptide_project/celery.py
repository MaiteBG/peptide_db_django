import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "peptide_project.settings")

app = Celery("peptide_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

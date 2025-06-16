from django.test import TestCase
import os
import django
import logging as log

from logs.logger_base import setup_logger
from proteins.services import get_proteins_from_organism, get_protein_metadata, create_proteins_from_metadata, \
    create_basic_database

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peptide_project.settings')
django.setup()

from catalog.models import Organism, Reference, Database, PeptideSequence

setup_logger("test.py")

create_basic_database()


# Crear bases de datos con nombres claros

def test_func():
    from celery import shared_task
    import time

    @shared_task
    def long_task():
        for i in range(10):
            print(f"Paso {i + 1}/10 completado")
            time.sleep(1)
            print("¡Tarea completada!")
        return "¡Tarea completada!"


# Ejecutar la prueba
test_func()


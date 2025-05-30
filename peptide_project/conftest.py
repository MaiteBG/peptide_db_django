# conftest.py en la raíz del proyecto

import os
import django


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peptide_project.settings')
    django.setup()

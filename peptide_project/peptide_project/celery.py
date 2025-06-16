import os
from pathlib import Path
import environ

from celery import Celery

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))

ENV_PATH = os.path.join(BASE_DIR.parent, '.env')
environ.Env.read_env(ENV_PATH)

project_name = env("PROJECT_NAME")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{project_name}.settings')

app = Celery(project_name)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

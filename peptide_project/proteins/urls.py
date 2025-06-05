# proteins/urls.py
from django.urls import path

from proteins.views import protein_list

urlpatterns = [
    path('protein_list', protein_list, name='protein-list'),
]

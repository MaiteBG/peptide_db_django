# proteins/urls.py
from django.urls import path

from proteins.views import protein_list, AddProteinView

urlpatterns = [
    path('protein_list', protein_list, name='protein-list'),
    path('add-proteins/', AddProteinView.as_view(), name='add-proteins-from-organism'),
]

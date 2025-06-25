# proteins/urls.py
from django.urls import path

from proteins import views
from proteins.views import protein_list, AddProteinView, get_progress

urlpatterns = [
    path('protein_list', protein_list, name='protein-list'),
    path('add-proteins/', AddProteinView.as_view(), name='add-proteins'),

]

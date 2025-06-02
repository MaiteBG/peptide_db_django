# proteins/urls.py
from django.urls import path

from proteins.views import ProteinsByOrganismView

urlpatterns = [
    path('by-organism/<slug:scientific_name>/', ProteinsByOrganismView.as_view(), name='proteins-by-organism')
]

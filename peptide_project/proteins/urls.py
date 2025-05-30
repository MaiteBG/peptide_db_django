# proteins/urls.py
from django.urls import path

from proteins.views import ProteinsByOrganismView

urlpatterns = [
    path('by-organism/<str:scientific_name>/', ProteinsByOrganismView.as_view(), name='proteins-by-organism')

]

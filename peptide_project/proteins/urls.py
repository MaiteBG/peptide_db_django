# proteins/urls.py
from django.urls import path

from proteins.views import protein_list, AddProteinView, start_task, get_progress, test_progress_page

urlpatterns = [
    path('protein_list', protein_list, name='protein-list'),
    path('add-proteins/', AddProteinView.as_view(), name='add-proteins-from-organism'),
    path("start-task/", start_task, name="start_task"),
    path("get-progress/<uuid:task_id>/", get_progress, name="get_progress"),
    path("test-progress/", test_progress_page, name="test_progress_page"),
]

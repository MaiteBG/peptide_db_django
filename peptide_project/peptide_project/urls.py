"""
URL configuration for peptide_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from catalog.views import OrganismListView
from proteins.views import get_progress

urlpatterns = [
    path("", OrganismListView.as_view(), name="home"),
    path('admin/', admin.site.urls),
    path("organisms/", OrganismListView.as_view(), name="organism-list"),
    path("proteins/", include("proteins.urls")),
    path("progress/<str:task_id>/", get_progress, name="get_progress")
]
